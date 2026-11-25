import json

from fastapi import HTTPException

from .store import create_day, encode, get_day


def timer_row(db, uid):
    row = db.execute('SELECT state FROM timers WHERE user_id=?', (uid,)).fetchone()
    return json.loads(row[0]) if row else None


def save_timer(db, uid, state):
    if state is None:
        db.execute('DELETE FROM timers WHERE user_id=?', (uid,))
    else:
        db.execute(
            'INSERT INTO timers VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET state=excluded.state',
            (uid, encode(state)),
        )
    return state


def elapsed(state, now):
    since = state['running_since']
    return state['elapsed'] + (max(0, now - since) if since is not None else 0)


def add_focus(db, uid, state, now, seconds):
    if seconds > 0:
        db.execute(
            'INSERT OR IGNORE INTO focus VALUES (?,?,?,?,?,?,?,?)',
            (
                uid,
                state['id'],
                state['date'],
                state['started_at'],
                now,
                seconds,
                state['mode'],
                encode(state['task']) if state['task'] else None,
            ),
        )


def break_state(state, now):
    return dict(
        state,
        stage='break',
        elapsed=0,
        running_since=now,
        duration=state['break_seconds'],
        revision=state['revision'] + 1,
    )


def settle(db, uid, state, now):
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


def start(db, uid, request, preferences, now, today):
    state = settle(db, uid, timer_row(db, uid), now)
    if state and state['id'] == request.id:
        return state
    if db.execute(
        'SELECT 1 FROM timer_requests WHERE user_id=? AND id=? UNION ALL SELECT 1 FROM focus WHERE user_id=? AND id=?',
        (uid, request.id, uid, request.id),
    ).fetchone():
        return state
    if state:
        raise HTTPException(409, '已有计时会话，请先结束')
    task = None
    if request.task_id:
        item = next((t for t in get_day(db, uid, today, today)['tasks'] if t['id'] == request.task_id), None)
        if not item:
            raise HTTPException(404, '任务已不在今天的计划中')
        task = {k: item[k] for k in ('id', 'title', 'category', 'category_name')}
    create_day(db, uid, today)
    db.execute('INSERT INTO timer_requests VALUES (?,?,?)', (uid, request.id, today))
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


def act(db, uid, request, now):
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
