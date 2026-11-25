import json

from ..core.exceptions import ConflictError, NotFoundError
from ..db.codec import encode, normalize_preferences
from ..db.repositories import focus as focus_repo, timers as timers_repo
from ..schemas.timer import TimerAction, TimerStart
from .days import day_allowed, ensure_day, get_day


def timer_row(db, uid: int) -> dict | None:
    raw = timers_repo.get_state_json(db, uid)
    return json.loads(raw) if raw else None


def save_timer(db, uid: int, state: dict | None) -> dict | None:
    if state is None:
        timers_repo.delete_state(db, uid)
    else:
        timers_repo.upsert_state_json(db, uid, encode(state))
    return state


def elapsed(state: dict, now: int) -> int:
    since = state['running_since']
    return state['elapsed'] + (max(0, now - since) if since is not None else 0)


def add_focus(db, uid: int, state: dict, now: int, seconds: int) -> None:
    if seconds > 0:
        focus_repo.insert_ignore(
            db,
            uid,
            state['id'],
            state['date'],
            state['started_at'],
            now,
            seconds,
            state['mode'],
            encode(state['task']) if state['task'] else None,
        )


def break_state(state: dict, now: int) -> dict:
    return dict(
        state,
        stage='break',
        elapsed=0,
        running_since=now,
        duration=state['break_seconds'],
        revision=state['revision'] + 1,
    )


def settle(db, uid: int, state: dict | None, now: int) -> dict | None:
    while state and state['running_since'] is not None and state['duration'] is not None:
        if elapsed(state, now) < state['duration']:
            break
        end = state['running_since'] + state['duration'] - state['elapsed']
        if state['stage'] == 'break':
            return save_timer(db, uid, None)
        add_focus(db, uid, state, end, state['duration'])
        if state['mode'] != 'pomodoro':
            return save_timer(db, uid, None)
        state = (
            break_state(state, end)
            if state['auto_break']
            else dict(state, stage='offer', elapsed=state['duration'], running_since=None, revision=state['revision'] + 1)
        )
        save_timer(db, uid, state)
    return state


def current_state(db, uid: int, now: int) -> dict | None:
    return settle(db, uid, timer_row(db, uid), now)


def timer_response(state: dict | None, timestamp: int, today: str) -> dict:
    return dict(timer=state, now=timestamp, today=today)


def start(db, user, request: TimerStart, now: int, today: str) -> dict:
    uid = user['id']
    day_allowed(request.date, today, True)
    preferences = normalize_preferences(json.loads(user['preferences']))
    state = settle(db, uid, timer_row(db, uid), now)
    if state and state['id'] == request.id:
        return state
    if focus_repo.exists_request_or_focus(db, uid, request.id):
        return state
    if state:
        raise ConflictError('已有计时会话，请先结束')
    task = None
    if request.task_id:
        item = next((t for t in get_day(db, uid, today, today)['tasks'] if t['id'] == request.task_id), None)
        if not item:
            raise NotFoundError('任务已不在今天的计划中')
        task = {k: item[k] for k in ('id', 'title', 'category', 'category_name')}
    ensure_day(db, uid, today)
    timers_repo.insert_request(db, uid, request.id, today)
    duration = (
        (request.minutes or preferences['focus_minutes']) * 60
        if request.mode == 'pomodoro'
        else (request.minutes or preferences['countdown_minutes']) * 60
        if request.mode == 'countdown'
        else None
    )
    return save_timer(
        db,
        uid,
        dict(
            id=request.id,
            date=today,
            revision=0,
            mode=request.mode,
            stage='focus',
            task=task,
            elapsed=0,
            running_since=now,
            started_at=now,
            duration=duration,
            auto_break=preferences['auto_break'],
            break_seconds=preferences['break_minutes'] * 60,
        ),
    )


def act(db, uid: int, request: TimerAction, now: int) -> dict | None:
    state = settle(db, uid, timer_row(db, uid), now)
    if not state or state['id'] != request.id or state['revision'] != request.revision:
        return state
    action = request.action
    if state['stage'] == 'offer':
        if action == 'start_break':
            return save_timer(db, uid, break_state(state, now))
        if action in ('dismiss', 'finish'):
            return save_timer(db, uid, None)
        return state
    if action == 'pause' and state['running_since'] is not None:
        return save_timer(
            db,
            uid,
            dict(state, running_since=None, elapsed=elapsed(state, now), revision=state['revision'] + 1),
        )
    if action == 'resume' and state['running_since'] is None:
        return save_timer(db, uid, dict(state, running_since=now, revision=state['revision'] + 1))
    if action == 'finish':
        if state['stage'] == 'focus':
            add_focus(db, uid, state, max(now, state['started_at']), elapsed(state, now))
        return save_timer(db, uid, None)
    return state
