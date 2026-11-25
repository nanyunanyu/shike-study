import hashlib
import json
import re
from datetime import timedelta

from fastapi import HTTPException

from . import messages


def overview(db, sender_id, date, timestamp):
    today = date.isoformat()
    week = [(date - timedelta(days=offset)).isoformat() for offset in range(6, -1, -1)]
    accounts = [
        dict(row)
        for row in db.execute(
            '''
            SELECT u.id, u.username, u.role, u.active, u.must_change,
                (SELECT max(date) FROM days WHERE user_id=u.id AND date<=? AND checked_at IS NOT NULL) AS last_checkin_date
            FROM users u ORDER BY u.id
            ''',
            (today,),
        )
    ]
    for row in accounts:
        row['active'] = bool(row['active'])
        row['must_change'] = bool(row['must_change'])
        row['checked_today'] = row['last_checkin_date'] == today

    checked = dict(
        db.execute(
            '''
            SELECT d.date, count(*) FROM days d JOIN users u ON d.user_id=u.id
            WHERE d.date BETWEEN ? AND ? AND d.checked_at IS NOT NULL AND u.role='user' AND u.active=1
            GROUP BY d.date
            ''',
            (week[0], today),
        )
    )
    focus = dict(
        db.execute(
            '''
            SELECT f.date, sum(f.seconds) FROM focus f JOIN users u ON f.user_id=u.id
            WHERE f.date BETWEEN ? AND ? AND u.role='user' AND u.active=1 GROUP BY f.date
            ''',
            (week[0], today),
        )
    )
    pending = db.execute(
        '''
        SELECT count(DISTINCT CASE WHEN dispatch_id IS NULL THEN -id ELSE dispatch_id END)
        FROM messages WHERE sender_id=? AND due_at>? AND canceled_at IS NULL
        ''',
        (sender_id, timestamp),
    ).fetchone()[0]
    return dict(
        date=today,
        active_accounts=sum(row['active'] and row['role'] == 'user' for row in accounts),
        checked_today=checked.get(today, 0),
        focus_seconds=focus.get(today, 0),
        pending_dispatches=pending,
        trend=[dict(date=day, checked=checked.get(day, 0), focus_seconds=focus.get(day, 0)) for day in week],
        accounts=accounts,
    )


def send(db, sender_id, payload, zone, timestamp):
    recipients = sorted(payload.recipient_ids)
    encoded = json.dumps([recipients, payload.kind, payload.body, payload.scheduled_for, payload.all_active])
    fingerprint = hashlib.sha256(encoded.encode()).hexdigest()
    previous = db.execute(
        'SELECT id, fingerprint FROM message_dispatches WHERE sender_id=? AND request_id=?',
        (sender_id, payload.request_id),
    ).fetchone()
    if previous:
        if previous['fingerprint'] != fingerprint:
            raise HTTPException(409, '发送请求与原内容不一致')
        remaining = db.execute('SELECT 1 FROM messages WHERE dispatch_id=? LIMIT 1', (previous['id'],)).fetchone()
        return {'key': f"batch-{previous['id']}" if remaining else None}

    valid = db.execute(
        '''
        SELECT count(*) FROM json_each(?) selected JOIN users u ON u.id=selected.value
        WHERE u.role='user' AND u.active=1
        ''',
        (json.dumps(recipients),),
    ).fetchone()[0]
    active_count = (
        db.execute("SELECT count(*) FROM users WHERE role='user' AND active=1").fetchone()[0]
        if payload.all_active
        else valid
    )
    if valid != len(recipients) or active_count != valid:
        raise HTTPException(409, '收件名单已变化。请核对名单后再发送。')
    due = messages.due_time(payload.scheduled_for, zone, timestamp)
    batch = db.execute(
        'INSERT INTO message_dispatches (sender_id,request_id,fingerprint,recipient_count) VALUES (?,?,?,?)',
        (sender_id, payload.request_id, fingerprint, len(recipients)),
    ).lastrowid
    messages.insert(db, sender_id, recipients, payload, timestamp, due, batch)
    return {'key': f'batch-{batch}'}


def _summary(row):
    signed_id = row['group_id']
    key = f'batch-{signed_id}' if signed_id > 0 else f'message-{-signed_id}'
    return dict(
        key=key,
        kind=row['kind'],
        body=row['body'],
        created_at=row['created_at'],
        due_at=row['due_at'],
        recipient_count=row['recipient_count'],
        pending=row['pending'],
        sent=row['sent'],
        canceled=row['canceled'],
        read=row['read'],
    )


_AGGREGATE = '''
    SELECT coalesce(m.dispatch_id,-m.id) AS group_id, m.kind, m.body, m.created_at, m.due_at,
        coalesce(d.recipient_count,1) AS recipient_count,
        sum(m.canceled_at IS NULL AND m.due_at>:now) AS pending,
        sum(m.canceled_at IS NULL AND m.due_at<=:now) AS sent,
        sum(m.canceled_at IS NOT NULL) AS canceled,
        sum(m.canceled_at IS NULL AND m.due_at<=:now AND m.read_at IS NOT NULL) AS read
    FROM messages m LEFT JOIN message_dispatches d ON m.dispatch_id=d.id
    WHERE m.sender_id=:sender
'''


def dispatches(db, sender_id, timestamp, status, kind, recipient_id, cursor):
    params = dict(sender=sender_id, now=timestamp, kind=kind, recipient=recipient_id)
    recipient_status = {
        'pending': 'm.canceled_at IS NULL AND m.due_at>:now',
        'sent': 'm.canceled_at IS NULL AND m.due_at<=:now',
        'canceled': 'm.canceled_at IS NOT NULL',
    }[status]
    compare, order = ('>', 'ASC') if status == 'pending' else ('<', 'DESC')
    boundary = ''
    if cursor is not None:
        if not re.fullmatch(r'[0-9]{1,18}:-?[0-9]{1,18}', cursor):
            raise HTTPException(422, '消息分页参数无效')
        params['due'], params['group_id'] = map(int, cursor.split(':'))
        boundary = f'AND (due_at, group_id) {compare} (:due, :group_id)'
    rows = db.execute(
        f'''
        WITH grouped AS (
            {_AGGREGATE} AND (:kind IS NULL OR m.kind=:kind)
            GROUP BY group_id HAVING :recipient IS NULL OR max(m.recipient_id=:recipient AND {recipient_status})=1
        ) SELECT * FROM grouped WHERE {status}>0 {boundary}
        ORDER BY due_at {order}, group_id {order} LIMIT 21
        ''',
        params,
    ).fetchall()
    next_cursor = f"{rows[19]['due_at']}:{rows[19]['group_id']}" if len(rows) > 20 else None
    return dict(items=[_summary(row) for row in rows[:20]], next_cursor=next_cursor)


def _key_filter(key):
    match = re.fullmatch(r'(batch|message)-([1-9][0-9]{0,17})', key)
    if not match:
        raise HTTPException(404, '消息记录不存在')
    target = int(match[2])
    if match[1] == 'batch':
        return 'm.dispatch_id=:target', target
    return 'm.id=:target AND m.dispatch_id IS NULL', target


def detail(db, sender_id, key, timestamp):
    condition, target = _key_filter(key)
    params = dict(sender=sender_id, now=timestamp, target=target)
    summary = db.execute(f'{_AGGREGATE} AND {condition} GROUP BY group_id', params).fetchone()
    if not summary:
        raise HTTPException(404, '消息记录不存在')
    recipients = [
        dict(row)
        for row in db.execute(
            f'''
            SELECT m.id AS message_id, u.id, u.username, m.read_at, m.canceled_at
            FROM messages m JOIN users u ON m.recipient_id=u.id
            WHERE m.sender_id=:sender AND {condition} ORDER BY u.username COLLATE NOCASE, u.id
            ''',
            params,
        )
    ]
    return dict(**_summary(summary), recipients=recipients)


def cancel(db, sender_id, key, timestamp):
    condition, target = _key_filter(key)
    record = detail(db, sender_id, key, timestamp)
    if not record['pending']:
        raise HTTPException(409, '没有可取消的待发消息')
    db.execute(
        f'''
        UPDATE messages AS m SET canceled_at=:now WHERE m.sender_id=:sender AND {condition}
        AND m.due_at>:now AND m.canceled_at IS NULL
        ''',
        dict(sender=sender_id, target=target, now=timestamp),
    )
    return dict(ok=True)
