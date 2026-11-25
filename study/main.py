import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager, suppress
from datetime import date
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, HTTPException, Path as PathParam, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import admin, extensions, messages, models as m, timing
from .reporting import export_backup, replace_backup, statistics, validate_backup
from .seed import BUILTINS, default_tasks
from .store import (
    HASHER,
    Store,
    create_day,
    create_user,
    day_row,
    day_tasks,
    encode,
    get_day,
    insert_adhoc_task,
    key,
    normalize_preferences,
    normalize_task,
    plan_row,
    unpack_plan,
    verify,
)

ROOT = Path(__file__).resolve().parent.parent
COOKIE = 'study_session'
SESSION_AGE = 7 * 86400
MAX_BODY = 16 * 1024 * 1024
MAX_SAFE_ID = 2**53 - 1
MessageID = Annotated[int, PathParam(gt=0, le=MAX_SAFE_ID)]
log = logging.getLogger(__name__)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def public_user(user):
    return dict(
        id=user['id'],
        username=user['username'],
        role=user['role'],
        active=bool(user['active']),
        must_change=bool(user['must_change']),
    )


def create_app(directory=None, clock=time.time):
    store = Store(directory or os.environ.get('STUDY_DATA_DIR', ROOT / 'data'))
    dummy = HASHER.hash(secrets.token_urlsafe())
    import_secret = secrets.token_bytes(32)

    def now():
        return int(clock())

    def today():
        return store.date(now()).isoformat()

    def maintenance():
        timestamp = now()
        with store.transaction(write=True) as db:
            db.execute('DELETE FROM sessions WHERE expires<=?', (timestamp,))
            db.execute('DELETE FROM timer_requests WHERE date<?', (store.date(timestamp).isoformat(),))
            for row in db.execute('SELECT user_id,state FROM timers').fetchall():
                timing.settle(db, row['user_id'], json.loads(row['state']), timestamp)
            initialized = db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone() is not None
        if not initialized:
            return
        store.snapshot(timestamp)

    @asynccontextmanager
    async def lifespan(_):
        store.initialize(os.environ.get('STUDY_TIMEZONE', 'Asia/Shanghai'))
        await asyncio.to_thread(maintenance)

        async def tick():
            while True:
                await asyncio.sleep(15)
                try:
                    await asyncio.to_thread(maintenance)
                except Exception:
                    log.exception('定时维护失败')

        worker = asyncio.create_task(tick())
        try:
            yield
        finally:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker

    app = FastAPI(title='拾刻学习', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store = store
    allowed_hosts = ['127.0.0.1', 'localhost', '[::1]', 'testserver']
    allowed_hosts += [item.strip() for item in os.environ.get('STUDY_ALLOWED_HOSTS', '').split(',') if item.strip()]
    public_origins = {
        item.strip().lower() for item in os.environ.get('STUDY_ALLOWED_ORIGINS', '').split(',') if item.strip()
    }
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    @app.middleware('http')
    async def policy(request, call_next):
        if request.url.path.startswith('/api/') and request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            host = request.headers.get('host', '').lower()
            origin = request.headers.get('origin')
            if origin and urlsplit(origin).netloc.lower() not in public_origins | {host}:
                return JSONResponse({'detail': '请求来源不匹配'}, status_code=403)
            if request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({'detail': '拒绝跨站请求'}, status_code=403)
            try:
                raw_size = int(request.headers.get('content-length', '0'))
            except ValueError:
                return JSONResponse({'detail': '请求长度无效'}, status_code=400)
            if raw_size < 0 or raw_size > MAX_BODY or (request.headers.get('transfer-encoding') and not raw_size):
                return JSONResponse({'detail': '请求过大或缺少长度'}, status_code=413)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_, error):
        return JSONResponse(
            {'detail': '输入或备份格式不正确', 'fields': [list(e['loc']) for e in error.errors()[:10]]},
            status_code=422,
        )

    @app.exception_handler(OverflowError)
    async def invalid_timestamp(_, error):
        return JSONResponse({'detail': '日期超出有效范围'}, status_code=422)

    def session(db, request, *, allow_change=False, admin=False):
        token = request.cookies.get(COOKIE, '')
        if len(token) != 43:
            raise HTTPException(401, '请先登录')
        row = db.execute(
            'SELECT users.*,sessions.csrf,sessions.token_hash FROM sessions JOIN users '
            'ON users.id=sessions.user_id WHERE token_hash=? AND expires>? AND active=1',
            (digest(token), now()),
        ).fetchone()
        if not row:
            raise HTTPException(401, '登录已失效')
        if request.method not in {'GET', 'HEAD', 'OPTIONS'} and not hmac.compare_digest(
            row['csrf'].encode(), request.headers.get('x-csrf-token', '').encode()
        ):
            raise HTTPException(403, '请求验证失败，请刷新页面')
        if row['must_change'] and not allow_change:
            raise HTTPException(403, '请先修改初始密码')
        if admin and row['role'] != 'admin':
            raise HTTPException(403, '仅超级管理员可访问')
        return row

    def view(request: Request):
        with store.transaction(read=True) as db:
            yield db, session(db, request)

    def mutate(request: Request):
        with store.transaction(write=True) as db:
            yield db, session(db, request)

    def admin_view(request: Request):
        with store.transaction(read=True) as db:
            yield db, session(db, request, admin=True)

    def admin_mutate(request: Request):
        with store.transaction(write=True) as db:
            yield db, session(db, request, admin=True)

    def delivery_view(request: Request):
        with store.transaction(write=True) as db:
            yield db, session(db, request)

    def bootstrap(user, csrf):
        return dict(
            user=public_user(user),
            csrf=csrf,
            today=today(),
            timezone=store.zone.key,
            preferences=normalize_preferences(json.loads(user['preferences'])),
        )

    @app.get('/api/status')
    def status():
        with store.transaction(read=True) as db:
            return dict(initialized=db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone() is not None)

    @app.post('/api/auth/login')
    def login(payload: m.Login, request: Request, response: Response):
        with store.transaction(write=True) as db:
            user = db.execute('SELECT * FROM users WHERE username=?', (payload.username,)).fetchone()
            timestamp = now()
            valid = verify(user['password'] if user and user['active'] else dummy, payload.password)
            if user and user['active'] and user['lock_until'] > timestamp:
                return JSONResponse(
                    {'detail': '登录失败次数过多，请稍后再试'},
                    status_code=429,
                    headers={'Retry-After': str(user['lock_until'] - timestamp)},
                )
            if not user or not user['active'] or not valid:
                if user and user['active']:
                    failures = (0 if user['lock_until'] else user['failures']) + 1
                    until = timestamp + 900 if failures >= 5 else 0
                    db.execute('UPDATE users SET failures=?,lock_until=? WHERE id=?', (failures, until, user['id']))
                    if until:
                        return JSONResponse(
                            {'detail': '登录失败次数过多，账号已暂时锁定'},
                            status_code=429,
                            headers={'Retry-After': '900'},
                        )
                return JSONResponse({'detail': '用户名或密码不正确，或账号已停用'}, status_code=401)
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            db.execute('UPDATE users SET failures=0,lock_until=0 WHERE id=?', (user['id'],))
            old = request.cookies.get(COOKIE)
            if old and len(old) == 43:
                db.execute('DELETE FROM sessions WHERE token_hash=? AND user_id=?', (digest(old), user['id']))
            db.execute('INSERT INTO sessions VALUES (?,?,?,?)', (digest(token), user['id'], csrf, timestamp + SESSION_AGE))
            response.set_cookie(
                COOKIE,
                token,
                max_age=SESSION_AGE,
                httponly=True,
                samesite='strict',
                secure=request.url.scheme == 'https',
            )
            return bootstrap(user, csrf)

    @app.get('/api/auth/me')
    def me(request: Request):
        with store.transaction(read=True) as db:
            user = session(db, request, allow_change=True)
            return bootstrap(user, user['csrf'])

    @app.post('/api/auth/logout')
    def logout(request: Request, response: Response):
        with store.transaction(write=True) as db:
            user = session(db, request, allow_change=True)
            db.execute('DELETE FROM sessions WHERE token_hash=?', (user['token_hash'],))
        response.delete_cookie(COOKIE, httponly=True, samesite='strict')
        return {'ok': True}

    @app.post('/api/auth/password')
    def password(payload: m.ChangePassword, request: Request):
        with store.transaction(write=True) as db:
            user = session(db, request, allow_change=True)
            if not verify(user['password'], payload.current):
                raise HTTPException(400, '原密码不正确')
            if payload.current == payload.password:
                raise HTTPException(422, '新密码不能与原密码相同')
            db.execute('UPDATE users SET password=?,must_change=0 WHERE id=?', (HASHER.hash(payload.password), user['id']))
            db.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?', (user['id'], user['token_hash']))
            return bootstrap(db.execute('SELECT * FROM users WHERE id=?', (user['id'],)).fetchone(), user['csrf'])

    @app.put('/api/preferences')
    def preferences(payload: m.Preferences, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        db.execute('UPDATE users SET preferences=? WHERE id=?', (encode(payload.model_dump()), user['id']))
        return payload

    def day_allowed(value, current, write=False):
        value = value.isoformat()
        if value > current:
            raise HTTPException(404, '不能查看未来日期')
        if write and value != current:
            raise HTTPException(409, '只能编辑今天，历史记录只读')
        return value

    @app.get('/api/days/{day}')
    def day_get(day: date, ctx=Depends(view, scope='function')):
        db, user = ctx
        current = today()
        return get_day(db, user['id'], day_allowed(day, current), current)

    def update_task(day, task_id, field, value, ctx):
        db, user = ctx
        current = today()
        day = day_allowed(day, current, True)
        uid = user['id']
        create_day(db, uid, day)
        tasks = [normalize_task(item) for item in json.loads(day_row(db, uid, day)['tasks'])]
        task = next((item for item in tasks if item['id'] == task_id), None)
        if not task:
            raise HTTPException(404, '任务不存在')
        task[field] = value
        db.execute('UPDATE days SET tasks=? WHERE user_id=? AND date=?', (encode(tasks), uid, day))
        return get_day(db, uid, day, current)

    @app.post('/api/days/{day}/tasks', status_code=201)
    def add_adhoc_task(day: date, payload: m.AdhocTaskInput, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        current = today()
        day_str = day_allowed(day, current, True)
        uid = user['id']
        names = {c['id']: c['name'] for c in json.loads(user['categories']) if not c['archived']}
        if payload.category not in names:
            raise HTTPException(422, '请选择未归档的分类')
        create_day(db, uid, day_str)
        tasks = [normalize_task(item) for item in json.loads(day_row(db, uid, day_str)['tasks'])]
        if len(tasks) >= 200:
            raise HTTPException(422, '当日任务数量已达上限')
        new_item = dict(
            id=f'adhoc-{key()[:12]}',
            title=payload.title,
            start=payload.start,
            end=payload.end,
            category=payload.category,
            category_name=names[payload.category],
            note=payload.note,
            estimate=payload.estimate,
            done=False,
            override=None,
            adhoc=True,
        )
        tasks = insert_adhoc_task(tasks, new_item)
        db.execute('UPDATE days SET tasks=? WHERE user_id=? AND date=?', (encode(tasks), uid, day_str))
        return get_day(db, uid, day_str, current)

    @app.put('/api/days/{day}/tasks/{task_id}')
    def edit_adhoc_task(day: date, task_id: m.Key, payload: m.AdhocTaskInput, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        current = today()
        day_str = day_allowed(day, current, True)
        uid = user['id']
        names = {c['id']: c['name'] for c in json.loads(user['categories']) if not c['archived']}
        if payload.category not in names:
            raise HTTPException(422, '请选择未归档的分类')
        create_day(db, uid, day_str)
        tasks = [normalize_task(item) for item in json.loads(day_row(db, uid, day_str)['tasks'])]
        task = next((item for item in tasks if item['id'] == task_id), None)
        if not task:
            raise HTTPException(404, '任务不存在')
        if not task.get('adhoc'):
            raise HTTPException(409, '计划模板任务请在「计划」页修改，或仅调整当天时段')
        task.update(
            title=payload.title,
            start=payload.start,
            end=payload.end,
            category=payload.category,
            category_name=names[payload.category],
            note=payload.note,
            estimate=payload.estimate,
            override=None,
        )
        db.execute('UPDATE days SET tasks=? WHERE user_id=? AND date=?', (encode(tasks), uid, day_str))
        return get_day(db, uid, day_str, current)

    @app.delete('/api/days/{day}/tasks/{task_id}')
    def delete_adhoc_task(day: date, task_id: m.Key, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        current = today()
        day_str = day_allowed(day, current, True)
        uid = user['id']
        create_day(db, uid, day_str)
        tasks = [normalize_task(item) for item in json.loads(day_row(db, uid, day_str)['tasks'])]
        task = next((item for item in tasks if item['id'] == task_id), None)
        if not task:
            raise HTTPException(404, '任务不存在')
        if not task.get('adhoc'):
            raise HTTPException(409, '只能删除当日临时任务')
        tasks = [item for item in tasks if item['id'] != task_id]
        db.execute('UPDATE days SET tasks=? WHERE user_id=? AND date=?', (encode(tasks), uid, day_str))
        return get_day(db, uid, day_str, current)

    @app.put('/api/days/{day}/tasks/{task_id}/done')
    def done(day: date, task_id: m.Key, payload: m.Toggle, ctx=Depends(mutate, scope='function')):
        return update_task(day, task_id, 'done', payload.done, ctx)

    @app.put('/api/days/{day}/tasks/{task_id}/times')
    def times(day: date, task_id: m.Key, payload: m.Times | None = None, ctx=Depends(mutate, scope='function')):
        return update_task(day, task_id, 'override', payload.model_dump() if payload else None, ctx)

    @app.put('/api/days/{day}/review')
    def review(day: date, payload: m.Review, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        current = today()
        day = day_allowed(day, current, True)
        create_day(db, user['id'], day)
        db.execute('UPDATE days SET review=? WHERE user_id=? AND date=?', (encode(payload.model_dump()), user['id'], day))
        return get_day(db, user['id'], day, current)

    @app.post('/api/days/{day}/check-in')
    def check_in(day: date, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        timestamp = now()
        current = store.date(timestamp).isoformat()
        day = day_allowed(day, current, True)
        create_day(db, user['id'], day)
        db.execute('UPDATE days SET checked_at=COALESCE(checked_at,?) WHERE user_id=? AND date=?', (timestamp, user['id'], day))
        return get_day(db, user['id'], day, current)

    @app.delete('/api/days/{day}/check-in')
    def undo_check_in(day: date, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        current = today()
        day = day_allowed(day, current, True)
        db.execute('UPDATE days SET checked_at=NULL WHERE user_id=? AND date=?', (user['id'], day))
        return get_day(db, user['id'], day, current)

    @app.get('/api/reviews')
    def reviews_timeline(
        mood: m.Mood | None = None,
        issue: m.Issue | None = None,
        q: Annotated[str | None, Query(max_length=100)] = None,
        before: date | None = None,
        limit: Annotated[int, Query(ge=1, le=50)] = 20,
        ctx=Depends(view, scope='function'),
    ):
        db, user = ctx
        return extensions.list_reviews(
            db,
            user['id'],
            today(),
            mood=mood,
            issue=issue,
            query=q,
            before=before.isoformat() if before else None,
            limit=limit,
        )

    @app.get('/api/milestones')
    def milestones_list(ctx=Depends(view, scope='function')):
        db, user = ctx
        return extensions.list_milestones(db, user['id'], today())

    @app.post('/api/milestones', status_code=201)
    def milestones_create(payload: m.MilestoneInput, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        timestamp = now()
        return extensions.create_milestone(db, user['id'], payload, timestamp, store.date(timestamp).isoformat())

    @app.put('/api/milestones/{milestone_id}')
    def milestones_update(milestone_id: m.Key, payload: m.MilestoneUpdate, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        return extensions.update_milestone(db, user['id'], milestone_id, payload, today())

    @app.delete('/api/milestones/{milestone_id}')
    def milestones_delete(milestone_id: m.Key, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        extensions.delete_milestone(db, user['id'], milestone_id)
        return {'ok': True}

    def get_plan(db, user, current):
        return dict(
            current=unpack_plan(plan_row(db, user['id'], current)),
            categories=json.loads(user['categories']),
            defaults=default_tasks(),
            history=[
                dict(row)
                for row in db.execute(
                    'SELECT id,date,created_at FROM plans WHERE user_id=? ORDER BY date DESC,created_at DESC,rowid DESC',
                    (user['id'],),
                )
            ],
        )

    @app.get('/api/plan')
    def plan(ctx=Depends(view, scope='function')):
        return get_plan(*ctx, today())

    @app.get('/api/plan/versions/{version}')
    def version(version: m.Key, ctx=Depends(view, scope='function')):
        db, user = ctx
        row = db.execute('SELECT * FROM plans WHERE user_id=? AND id=?', (user['id'], version)).fetchone()
        if not row:
            raise HTTPException(404, '计划版本不存在')
        return unpack_plan(row)

    @app.put('/api/plan')
    def save_plan(payload: m.PlanInput, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        timestamp = now()
        current = store.date(timestamp).isoformat()
        uid = user['id']
        old = plan_row(db, uid, current)
        if old['id'] != payload.base:
            raise HTTPException(409, '计划已在其他页面更新，请刷新后重试')
        names = {c['id']: c['name'] for c in json.loads(user['categories']) if not c['archived']}
        if any(t.category not in names for t in payload.tasks):
            raise HTTPException(422, '请为每个任务选择未归档的分类')
        tasks = [dict(t.model_dump(), category_name=names[t.category]) for t in payload.tasks]
        if json.loads(old['tasks']) != tasks:
            db.execute('INSERT INTO plans VALUES (?,?,?,?,?)', (uid, key(), current, timestamp, encode(tasks)))
            row = day_row(db, uid, current)
            if row:
                db.execute(
                    'UPDATE days SET tasks=? WHERE user_id=? AND date=?',
                    (encode(day_tasks(tasks, json.loads(row['tasks']))), uid, current),
                )
        return get_plan(db, user, current)

    @app.put('/api/categories')
    def save_categories(payload: m.CategoriesInput, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        current = today()
        old = {c['id']: c for c in json.loads(user['categories'])}
        cats = {c.id: c.model_dump() for c in payload.categories}
        builtin_ids = {c['id'] for c in BUILTINS}
        if any(cats.get(c['id']) != c for c in BUILTINS) or any(
            c['builtin'] != (c['id'] in builtin_ids) for c in cats.values()
        ):
            raise HTTPException(422, '不能修改内置分类')
        if not old.keys() <= cats.keys():
            raise HTTPException(422, '分类只能归档，不能删除')
        live = [c['name'].casefold() for c in cats.values() if not c['archived']]
        if len(live) != len(set(live)):
            raise HTTPException(422, '分类名称不能重复')
        if any(cats[t['category']]['archived'] for t in json.loads(plan_row(db, user['id'], current)['tasks'])):
            raise HTTPException(409, '请先在当前计划中迁移该分类下的任务')
        db.execute('UPDATE users SET categories=? WHERE id=?', (encode(list(cats.values())), user['id']))
        return list(cats.values())

    def timer_state(db, uid, timestamp):
        return timing.settle(db, uid, timing.timer_row(db, uid), timestamp)

    def timer_response(state, timestamp):
        return dict(timer=state, now=timestamp, today=store.date(timestamp).isoformat())

    @app.get('/api/timer')
    def timer(ctx=Depends(mutate, scope='function')):
        db, user = ctx
        timestamp = now()
        return timer_response(timer_state(db, user['id'], timestamp), timestamp)

    @app.post('/api/timer/start')
    def start(payload: m.TimerStart, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        timestamp = now()
        current = store.date(timestamp).isoformat()
        day_allowed(payload.date, current, True)
        prefs = normalize_preferences(json.loads(user['preferences']))
        return timer_response(timing.start(db, user['id'], payload, prefs, timestamp, current), timestamp)

    @app.post('/api/timer/action')
    def action(payload: m.TimerAction, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        timestamp = now()
        return timer_response(timing.act(db, user['id'], payload, timestamp), timestamp)

    @app.get('/api/statistics')
    def stats(ctx=Depends(view, scope='function')):
        db, user = ctx
        return statistics(db, user['id'], today())

    @app.get('/api/backup')
    def backup(ctx=Depends(view, scope='function')):
        return export_backup(*ctx)

    def import_token(user, payload):
        message = f"{user['id']}:{user['token_hash']}:" + encode(payload.model_dump(mode='json'))
        return hmac.new(import_secret, message.encode(), hashlib.sha256).hexdigest()

    @app.post('/api/backup/preview')
    def preview(payload: m.Backup, ctx=Depends(view, scope='function')):
        _, user = ctx
        return dict(counts=validate_backup(payload, store, today()), token=import_token(user, payload))

    @app.put('/api/backup')
    def import_backup(payload: m.ImportCommit, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        counts = validate_backup(payload.backup, store, today())
        if not hmac.compare_digest(payload.token, import_token(user, payload.backup)):
            raise HTTPException(409, '请重新预览要导入的备份')
        if timer_state(db, user['id'], now()):
            raise HTTPException(409, '请先结束计时器及休息阶段')
        name = f"{today()}-account-{user['id']}-{key()}.json"
        store.write_private('rollback', name, encode(export_backup(db, user)).encode())
        replace_backup(db, user['id'], payload.backup)
        return dict(counts=counts, preferences=payload.backup.preferences)

    def find_user(db, uid, *, writable=False):
        row = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
        if not row:
            raise HTTPException(404, '账号不存在')
        if writable and row['role'] != 'user':
            raise HTTPException(403, '不能在后台修改超级管理员账号')
        return row

    @app.get('/api/messages/status')
    def message_status(ctx=Depends(delivery_view, scope='function')):
        db, user = ctx
        return messages.status(db, user['id'], now())

    @app.get('/api/messages')
    def message_inbox(
        before: Annotated[int | None, Query(gt=0, le=MAX_SAFE_ID)] = None,
        ctx=Depends(delivery_view, scope='function'),
    ):
        db, user = ctx
        return messages.inbox(db, user['id'], now(), before)

    @app.post('/api/messages/preview')
    def message_preview(ctx=Depends(mutate, scope='function')):
        db, user = ctx
        return messages.claim_preview(db, user['id'], now())

    @app.put('/api/messages/{message_id}/read')
    def read_message(message_id: MessageID, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        return messages.read(db, user['id'], message_id, now())

    @app.delete('/api/messages/{message_id}')
    def delete_message(message_id: MessageID, ctx=Depends(mutate, scope='function')):
        db, user = ctx
        messages.delete_from_inbox(db, user['id'], message_id, now())
        return {'ok': True}

    @app.get('/api/admin/users/{uid}/messages/sent')
    def sent_messages(
        uid: int,
        before: Annotated[int | None, Query(gt=0, le=MAX_SAFE_ID)] = None,
        ctx=Depends(admin_view, scope='function'),
    ):
        db, admin_user = ctx
        find_user(db, uid, writable=True)
        return messages.sent(db, admin_user['id'], uid, now(), before)

    @app.get('/api/admin/users/{uid}/messages')
    def pending_messages(uid: int, ctx=Depends(admin_view, scope='function')):
        db, admin_user = ctx
        find_user(db, uid, writable=True)
        return messages.pending(db, admin_user['id'], uid, now())

    @app.post('/api/admin/users/{uid}/messages', status_code=201)
    def create_message(uid: int, payload: m.NewMessage, ctx=Depends(admin_mutate, scope='function')):
        db, admin_user = ctx
        if not find_user(db, uid, writable=True)['active']:
            raise HTTPException(409, '账号已停用，不能发送新消息')
        timestamp = now()
        due = messages.due_time(payload.scheduled_for, store.zone, timestamp)
        message_id = messages.insert(db, admin_user['id'], (uid,), payload, timestamp, due)
        return messages.serialize(messages.get(db, message_id), recipient=False)

    @app.delete('/api/admin/users/{uid}/messages/{message_id}')
    def cancel_message(uid: int, message_id: MessageID, ctx=Depends(admin_mutate, scope='function')):
        db, admin_user = ctx
        row = messages.get(db, message_id)
        if not row or row['sender_id'] != admin_user['id'] or row['recipient_id'] != uid or row['canceled_at'] is not None:
            raise HTTPException(404, '消息不存在')
        timestamp = now()
        if row['due_at'] <= timestamp:
            raise HTTPException(409, '定时消息已到点，无法取消')
        db.execute('UPDATE messages SET canceled_at=? WHERE id=?', (timestamp, message_id))
        return {'ok': True}

    @app.get('/api/admin/overview')
    def admin_overview(ctx=Depends(admin_view, scope='function')):
        db, user = ctx
        timestamp = now()
        return admin.overview(db, user['id'], store.date(timestamp), timestamp)

    @app.get('/api/admin/dispatches')
    def admin_dispatches(
        status: Literal['pending', 'sent', 'canceled'] = 'pending',
        kind: Literal['reminder', 'encouragement'] | None = None,
        recipient_id: Annotated[int | None, Query(gt=0, le=MAX_SAFE_ID)] = None,
        cursor: Annotated[str | None, Query(max_length=64)] = None,
        ctx=Depends(admin_view, scope='function'),
    ):
        db, user = ctx
        return admin.dispatches(db, user['id'], now(), status, kind, recipient_id, cursor)

    @app.post('/api/admin/dispatches', status_code=201)
    def admin_send(payload: m.NewDispatch, ctx=Depends(admin_mutate, scope='function')):
        db, user = ctx
        return admin.send(db, user['id'], payload, store.zone, now())

    @app.get('/api/admin/dispatches/{key}')
    def admin_dispatch(key: str, ctx=Depends(admin_view, scope='function')):
        db, user = ctx
        return admin.detail(db, user['id'], key, now())

    @app.delete('/api/admin/dispatches/{key}')
    def admin_cancel_dispatch(key: str, ctx=Depends(admin_mutate, scope='function')):
        db, user = ctx
        return admin.cancel(db, user['id'], key, now())

    @app.get('/api/admin/users')
    def users(ctx=Depends(admin_view, scope='function')):
        db, _ = ctx
        return [public_user(row) for row in db.execute('SELECT * FROM users ORDER BY id')]

    @app.post('/api/admin/users', status_code=201)
    def new_user(payload: m.NewUser, ctx=Depends(admin_mutate, scope='function')):
        db, _ = ctx
        timestamp = now()
        try:
            uid = create_user(
                db,
                username=payload.username,
                password=payload.password,
                role='user',
                must_change=payload.must_change,
                today=store.date(timestamp).isoformat(),
                now=timestamp,
            )
        except sqlite3.IntegrityError as error:
            raise HTTPException(409, '用户名已存在') from error
        return public_user(find_user(db, uid))

    @app.put('/api/admin/users/{uid}/active')
    def user_active(uid: int, payload: m.UserActive, ctx=Depends(admin_mutate, scope='function')):
        db, _ = ctx
        find_user(db, uid, writable=True)
        db.execute('UPDATE users SET active=? WHERE id=?', (payload.active, uid))
        if not payload.active:
            db.execute('DELETE FROM sessions WHERE user_id=?', (uid,))
        return public_user(find_user(db, uid))

    @app.put('/api/admin/users/{uid}/password')
    def user_password(uid: int, payload: m.ResetPassword, ctx=Depends(admin_mutate, scope='function')):
        db, _ = ctx
        find_user(db, uid, writable=True)
        db.execute(
            'UPDATE users SET password=?,must_change=?,failures=0,lock_until=0 WHERE id=?',
            (HASHER.hash(payload.password), payload.must_change, uid),
        )
        db.execute('DELETE FROM sessions WHERE user_id=?', (uid,))
        return public_user(find_user(db, uid))

    @app.delete('/api/admin/users/{uid}')
    def delete_user(uid: int, ctx=Depends(admin_mutate, scope='function')):
        db, _ = ctx
        find_user(db, uid, writable=True)
        db.execute('DELETE FROM users WHERE id=?', (uid,))
        return {'ok': True}

    @app.get('/api/admin/users/{uid}/day/{day}')
    def admin_day(uid: int, day: date, ctx=Depends(admin_view, scope='function')):
        db, _ = ctx
        find_user(db, uid)
        current = today()
        return get_day(db, uid, day_allowed(day, current), current, editable=False)

    @app.get('/api/admin/users/{uid}/plan')
    def admin_plan(uid: int, ctx=Depends(admin_view, scope='function')):
        db, _ = ctx
        return get_plan(db, find_user(db, uid), today())

    @app.get('/api/admin/users/{uid}/statistics')
    def admin_statistics(uid: int, ctx=Depends(admin_view, scope='function')):
        db, _ = ctx
        find_user(db, uid)
        return statistics(db, uid, today())

    dist = ROOT / 'webui'
    if not (dist / 'index.html').is_file():
        dist = ROOT / 'dist'
    if (dist / 'assets').is_dir():
        app.mount('/assets', StaticFiles(directory=dist / 'assets'), name='assets')

    @app.get('/{path:path}')
    def frontend(path: str):
        if path == 'api' or path.startswith(('api/', 'assets/')):
            raise HTTPException(404)
        if path == 'favicon.svg' and (dist / 'favicon.svg').is_file():
            return FileResponse(dist / 'favicon.svg')
        if (dist / 'index.html').is_file():
            return FileResponse(dist / 'index.html', headers={'Cache-Control': 'no-cache'})
        return Response('前端尚未构建，请先运行 npm install && npm run build。', media_type='text/plain', status_code=503)

    return app


app = create_app()
