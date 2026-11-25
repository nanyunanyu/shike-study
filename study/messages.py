from datetime import datetime

from fastapi import HTTPException


def due_time(value, zone, now):
    if value is None:
        return now
    try:
        local = datetime.fromisoformat(value)
        candidates = set()
        for fold in (0, 1):
            instant = int(local.replace(tzinfo=zone, fold=fold).timestamp())
            if datetime.fromtimestamp(instant, zone).replace(tzinfo=None) == local:
                candidates.add(instant)
    except (ValueError, OverflowError, OSError) as error:
        raise HTTPException(422, '定时日期无效') from error
    if len(candidates) != 1:
        raise HTTPException(422, '该时间在学习系统时区不存在或重复，请选择其他时间')
    due = candidates.pop()
    if due <= now:
        raise HTTPException(422, '定时发送时间须晚于当前时间')
    return due


_COLUMNS = 'messages.*,users.username AS sender'
_JOIN = 'FROM messages JOIN users ON users.id=messages.sender_id'
_DELIVERED = 'recipient_id=? AND due_at<=? AND canceled_at IS NULL'
_VISIBLE = 'recipient_deleted_at IS NULL'
_UNREAD = f'{_DELIVERED} AND {_VISIBLE} AND read_at IS NULL'
_NEEDS_PREVIEW = f'{_UNREAD} AND previewed_at IS NULL'


def serialize(row, *, recipient=True):
    keys = ['id', 'sender', 'kind', 'body', 'created_at', 'due_at']
    if recipient:
        keys.append('read_at')
    return {key: row[key] for key in keys}


def get(db, message_id):
    return db.execute(f'SELECT {_COLUMNS} {_JOIN} WHERE messages.id=?', (message_id,)).fetchone()


def status(db, uid, now):
    unread, pending = db.execute(
        f'SELECT count(*),count(*)-count(previewed_at) FROM messages WHERE {_UNREAD}', (uid, now)
    ).fetchone()
    return dict(unread=unread, pending=bool(pending))


def read(db, uid, message_id, now):
    result = db.execute(
        f'UPDATE messages SET read_at=coalesce(read_at,?) WHERE id=? AND {_DELIVERED} AND {_VISIBLE}',
        (now, message_id, uid, now),
    )
    if not result.rowcount:
        raise HTTPException(404, '消息不存在')
    return serialize(get(db, message_id))


def delete_from_inbox(db, uid, message_id, now):
    result = db.execute(
        f'UPDATE messages SET recipient_deleted_at=coalesce(recipient_deleted_at,?) WHERE id=? AND {_DELIVERED}',
        (now, message_id, uid, now),
    )
    if not result.rowcount:
        raise HTTPException(404, '消息不存在')


def _page(db, scope, params, before, *, recipient):
    where = scope
    if before is not None:
        cursor = db.execute(f'SELECT due_at FROM messages WHERE id=? AND {scope}', (before, *params)).fetchone()
        if not cursor:
            raise HTTPException(404, '消息不存在')
        where += ' AND (due_at,messages.id)<(?,?)'
        params += (cursor['due_at'], before)
    if recipient:
        where += f' AND {_VISIBLE}'
    rows = db.execute(
        f'SELECT {_COLUMNS} {_JOIN} WHERE {where} ORDER BY due_at DESC,messages.id DESC LIMIT 21', params
    ).fetchall()
    return dict(
        items=[serialize(row, recipient=recipient) for row in rows[:20]],
        next_before=rows[19]['id'] if len(rows) > 20 else None,
    )


def inbox(db, uid, now, before):
    return _page(db, _DELIVERED, (uid, now), before, recipient=True)


def sent(db, sender_id, uid, now, before):
    return _page(db, f'sender_id=? AND {_DELIVERED}', (sender_id, uid, now), before, recipient=False)


def pending(db, sender_id, uid, now):
    return [
        serialize(row, recipient=False)
        for row in db.execute(
            f'SELECT {_COLUMNS} {_JOIN} WHERE sender_id=? AND recipient_id=? AND due_at>? AND canceled_at IS NULL '
            'ORDER BY due_at,messages.id',
            (sender_id, uid, now),
        )
    ]


def claim_preview(db, uid, now):
    latest = db.execute(
        f'SELECT {_COLUMNS} {_JOIN} WHERE {_NEEDS_PREVIEW} ORDER BY due_at DESC,messages.id DESC LIMIT 1',
        (uid, now),
    ).fetchone()
    if not latest:
        return None
    count = db.execute(f'UPDATE messages SET previewed_at=? WHERE {_NEEDS_PREVIEW}', (now, uid, now)).rowcount
    return dict(message=serialize(latest), more=count - 1)


def insert(db, sender_id, recipient_ids, payload, timestamp, due, dispatch_id=None):
    sql = 'INSERT INTO messages (sender_id,recipient_id,kind,body,created_at,due_at,dispatch_id) VALUES (?,?,?,?,?,?,?)'
    rows = ((sender_id, uid, payload.kind, payload.body, timestamp, due, dispatch_id) for uid in recipient_ids)
    if dispatch_id is not None:
        db.executemany(sql, rows)
        return None
    return db.execute(sql, next(rows)).lastrowid
