import json
from datetime import date

from ..core.exceptions import ConflictError, NotFoundError, ValidationDomainError
from ..core.security import new_key
from ..db.codec import encode, normalize_review, normalize_task, unpack_focus
from ..db.repositories import days as days_repo, focus as focus_repo, plans as plans_repo
from ..schemas.days import AdhocTaskInput, Review, Times


def day_allowed(value: date, current: str, write: bool = False) -> str:
    iso = value.isoformat()
    if iso > current:
        raise NotFoundError('不能查看未来日期')
    if write and iso != current:
        raise ConflictError('只能编辑今天，历史记录只读')
    return iso


def insert_adhoc_task(tasks: list[dict], item: dict) -> list[dict]:
    target_start = (item.get('override') or item)['start']
    result = list(tasks)
    insert_at = len(result)
    for index, existing in enumerate(result):
        existing_start = (existing.get('override') or existing)['start']
        if existing_start > target_start:
            insert_at = index
            break
    result.insert(insert_at, item)
    return result


def merge_day_tasks(tasks: list[dict], previous=()) -> list[dict]:
    old = {item['id']: item for item in previous}
    merged = [
        dict(
            item,
            done=old.get(item['id'], {}).get('done', False),
            override=old.get(item['id'], {}).get('override'),
            adhoc=False,
        )
        for item in tasks
    ]
    plan_ids = {item['id'] for item in merged}
    for item in previous:
        if item.get('adhoc') and item['id'] not in plan_ids:
            merged = insert_adhoc_task(merged, normalize_task(item))
    return merged


def ensure_day(db, uid: int, day: str) -> None:
    plan = plans_repo.get_effective(db, uid, day)
    tasks = merge_day_tasks(json.loads(plan['tasks'])) if plan else []
    days_repo.insert_ignore(db, uid, day, encode(tasks), encode(Review().model_dump()))


def get_day(db, uid: int, day: str, today: str, *, editable: bool = True) -> dict:
    row = days_repo.get(db, uid, day)
    focus = []
    if row:
        tasks = [normalize_task(t) for t in json.loads(row['tasks'])]
        review = normalize_review(json.loads(row['review']))
        focus = [unpack_focus(s) for s in focus_repo.list_by_day(db, uid, day)]
    else:
        plan = plans_repo.get_effective(db, uid, day) if day == today else None
        tasks = merge_day_tasks(json.loads(plan['tasks'])) if plan else []
        review = Review().model_dump()
    return dict(
        date=day,
        today=today,
        exists=bool(row),
        editable=editable and day == today,
        tasks=tasks,
        review=review,
        checked_at=row['checked_at'] if row else None,
        focus=focus,
        focus_seconds=sum(s['seconds'] for s in focus),
    )


def get_day_for_date(db, uid: int, day: date, current: str, *, editable: bool = True) -> dict:
    return get_day(db, uid, day_allowed(day, current), current, editable=editable)


def _update_task_field(db, uid: int, day: date, task_id: str, field: str, value, current: str) -> dict:
    day_str = day_allowed(day, current, True)
    ensure_day(db, uid, day_str)
    tasks = [normalize_task(item) for item in json.loads(days_repo.get(db, uid, day_str)['tasks'])]
    task = next((item for item in tasks if item['id'] == task_id), None)
    if not task:
        raise NotFoundError('任务不存在')
    task[field] = value
    days_repo.update_tasks(db, uid, day_str, encode(tasks))
    return get_day(db, uid, day_str, current)


def add_adhoc_task(db, user, day: date, payload: AdhocTaskInput, current: str) -> dict:
    day_str = day_allowed(day, current, True)
    uid = user['id']
    names = {c['id']: c['name'] for c in json.loads(user['categories']) if not c['archived']}
    if payload.category not in names:
        raise ValidationDomainError('请选择未归档的分类')
    ensure_day(db, uid, day_str)
    tasks = [normalize_task(item) for item in json.loads(days_repo.get(db, uid, day_str)['tasks'])]
    if len(tasks) >= 200:
        raise ValidationDomainError('当日任务数量已达上限')
    new_item = dict(
        id=f'adhoc-{new_key()[:12]}',
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
    days_repo.update_tasks(db, uid, day_str, encode(tasks))
    return get_day(db, uid, day_str, current)


def edit_adhoc_task(db, user, day: date, task_id: str, payload: AdhocTaskInput, current: str) -> dict:
    day_str = day_allowed(day, current, True)
    uid = user['id']
    names = {c['id']: c['name'] for c in json.loads(user['categories']) if not c['archived']}
    if payload.category not in names:
        raise ValidationDomainError('请选择未归档的分类')
    ensure_day(db, uid, day_str)
    tasks = [normalize_task(item) for item in json.loads(days_repo.get(db, uid, day_str)['tasks'])]
    task = next((item for item in tasks if item['id'] == task_id), None)
    if not task:
        raise NotFoundError('任务不存在')
    if not task.get('adhoc'):
        raise ConflictError('计划模板任务请在「计划」页修改，或仅调整当天时段')
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
    days_repo.update_tasks(db, uid, day_str, encode(tasks))
    return get_day(db, uid, day_str, current)


def delete_adhoc_task(db, uid: int, day: date, task_id: str, current: str) -> dict:
    day_str = day_allowed(day, current, True)
    ensure_day(db, uid, day_str)
    tasks = [normalize_task(item) for item in json.loads(days_repo.get(db, uid, day_str)['tasks'])]
    task = next((item for item in tasks if item['id'] == task_id), None)
    if not task:
        raise NotFoundError('任务不存在')
    if not task.get('adhoc'):
        raise ConflictError('只能删除当日临时任务')
    tasks = [item for item in tasks if item['id'] != task_id]
    days_repo.update_tasks(db, uid, day_str, encode(tasks))
    return get_day(db, uid, day_str, current)


def toggle_task_done(db, uid: int, day: date, task_id: str, done: bool, current: str) -> dict:
    return _update_task_field(db, uid, day, task_id, 'done', done, current)


def override_task_times(db, uid: int, day: date, task_id: str, payload: Times | None, current: str) -> dict:
    return _update_task_field(db, uid, day, task_id, 'override', payload.model_dump() if payload else None, current)


def save_review(db, uid: int, day: date, payload: Review, current: str) -> dict:
    day_str = day_allowed(day, current, True)
    ensure_day(db, uid, day_str)
    days_repo.update_review(db, uid, day_str, encode(payload.model_dump()))
    return get_day(db, uid, day_str, current)


def check_in(db, uid: int, day: date, timestamp: int, current: str) -> dict:
    day_str = day_allowed(day, current, True)
    ensure_day(db, uid, day_str)
    days_repo.set_checked_at_if_null(db, uid, day_str, timestamp)
    return get_day(db, uid, day_str, current)


def undo_check_in(db, uid: int, day: date, current: str) -> dict:
    day_str = day_allowed(day, current, True)
    days_repo.clear_checked_at(db, uid, day_str)
    return get_day(db, uid, day_str, current)
