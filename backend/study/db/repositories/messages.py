import sqlite3

_COLUMNS = 'messages.*,users.username AS sender'
_JOIN = 'FROM messages JOIN users ON users.id=messages.sender_id'
_DELIVERED = 'recipient_id=? AND due_at<=? AND canceled_at IS NULL'
_VISIBLE = 'recipient_deleted_at IS NULL'
_UNREAD = f'{_DELIVERED} AND {_VISIBLE} AND read_at IS NULL'
_NEEDS_PREVIEW = f'{_UNREAD} AND previewed_at IS NULL'

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


def get_with_sender(db: sqlite3.Connection, message_id: int):
    return db.execute(f'SELECT {_COLUMNS} {_JOIN} WHERE messages.id=?', (message_id,)).fetchone()


def get_unread_and_preview_counts(db: sqlite3.Connection, uid: int, now: int) -> tuple[int, int]:
    row = db.execute(
        f'SELECT count(*),count(*)-count(previewed_at) FROM messages WHERE {_UNREAD}',
        (uid, now),
    ).fetchone()
    return row[0], row[1]


def mark_read(db: sqlite3.Connection, uid: int, message_id: int, now: int) -> int:
    return db.execute(
        f'UPDATE messages SET read_at=coalesce(read_at,?) WHERE id=? AND {_DELIVERED} AND {_VISIBLE}',
        (now, message_id, uid, now),
    ).rowcount


def soft_delete_inbox(db: sqlite3.Connection, uid: int, message_id: int, now: int) -> int:
    return db.execute(
        f'UPDATE messages SET recipient_deleted_at=coalesce(recipient_deleted_at,?) WHERE id=? AND {_DELIVERED}',
        (now, message_id, uid, now),
    ).rowcount


def _page(db: sqlite3.Connection, scope: str, params: tuple, before: int | None, *, recipient: bool):
    where = scope
    query_params = params
    if before is not None:
        cursor = db.execute(f'SELECT due_at FROM messages WHERE id=? AND {scope}', (before, *params)).fetchone()
        if not cursor:
            return None
        where += ' AND (due_at,messages.id)<(?,?)'
        query_params = (*params, cursor['due_at'], before)
    if recipient:
        where += f' AND {_VISIBLE}'
    return db.execute(
        f'SELECT {_COLUMNS} {_JOIN} WHERE {where} ORDER BY due_at DESC,messages.id DESC LIMIT 21',
        query_params,
    ).fetchall()


def list_inbox_page(db: sqlite3.Connection, uid: int, now: int, before: int | None):
    return _page(db, _DELIVERED, (uid, now), before, recipient=True)


def list_sent_page(db: sqlite3.Connection, sender_id: int, uid: int, now: int, before: int | None):
    return _page(db, f'sender_id=? AND {_DELIVERED}', (sender_id, uid, now), before, recipient=False)


def list_pending_for_recipient(db: sqlite3.Connection, sender_id: int, uid: int, now: int):
    return db.execute(
        f'SELECT {_COLUMNS} {_JOIN} WHERE sender_id=? AND recipient_id=? AND due_at>? AND canceled_at IS NULL '
        'ORDER BY due_at,messages.id',
        (sender_id, uid, now),
    ).fetchall()


def claim_preview(db: sqlite3.Connection, uid: int, now: int):
    latest = db.execute(
        f'SELECT {_COLUMNS} {_JOIN} WHERE {_NEEDS_PREVIEW} ORDER BY due_at DESC,messages.id DESC LIMIT 1',
        (uid, now),
    ).fetchone()
    if not latest:
        return None, 0
    count = db.execute(f'UPDATE messages SET previewed_at=? WHERE {_NEEDS_PREVIEW}', (now, uid, now)).rowcount
    return latest, count


def insert_single(
    db: sqlite3.Connection,
    sender_id: int,
    recipient_id: int,
    kind: str,
    body: str,
    created_at: int,
    due_at: int,
) -> int:
    return db.execute(
        'INSERT INTO messages (sender_id,recipient_id,kind,body,created_at,due_at,dispatch_id) VALUES (?,?,?,?,?,?,NULL)',
        (sender_id, recipient_id, kind, body, created_at, due_at),
    ).lastrowid


def insert_batch(
    db: sqlite3.Connection,
    sender_id: int,
    recipient_ids,
    kind: str,
    body: str,
    created_at: int,
    due_at: int,
    dispatch_id: int,
) -> None:
    db.executemany(
        'INSERT INTO messages (sender_id,recipient_id,kind,body,created_at,due_at,dispatch_id) VALUES (?,?,?,?,?,?,?)',
        ((sender_id, uid, kind, body, created_at, due_at, dispatch_id) for uid in recipient_ids),
    )


def cancel_single(db: sqlite3.Connection, message_id: int, canceled_at: int) -> None:
    db.execute('UPDATE messages SET canceled_at=? WHERE id=?', (canceled_at, message_id))


def count_pending_groups(db: sqlite3.Connection, sender_id: int, timestamp: int) -> int:
    return db.execute(
        '''
        SELECT count(DISTINCT CASE WHEN dispatch_id IS NULL THEN -id ELSE dispatch_id END)
        FROM messages WHERE sender_id=? AND due_at>? AND canceled_at IS NULL
        ''',
        (sender_id, timestamp),
    ).fetchone()[0]


def find_dispatch_by_request(db: sqlite3.Connection, sender_id: int, request_id: str):
    return db.execute(
        'SELECT id, fingerprint FROM message_dispatches WHERE sender_id=? AND request_id=?',
        (sender_id, request_id),
    ).fetchone()


def has_dispatch_messages(db: sqlite3.Connection, dispatch_id: int) -> bool:
    return db.execute('SELECT 1 FROM messages WHERE dispatch_id=? LIMIT 1', (dispatch_id,)).fetchone() is not None


def insert_dispatch(
    db: sqlite3.Connection,
    sender_id: int,
    request_id: str,
    fingerprint: str,
    recipient_count: int,
) -> int:
    return db.execute(
        'INSERT INTO message_dispatches (sender_id,request_id,fingerprint,recipient_count) VALUES (?,?,?,?)',
        (sender_id, request_id, fingerprint, recipient_count),
    ).lastrowid


def list_dispatch_groups(
    db: sqlite3.Connection,
    sender_id: int,
    timestamp: int,
    status: str,
    kind: str | None,
    recipient_id: int | None,
    boundary_due: int | None = None,
    boundary_group_id: int | None = None,
):
    params = dict(sender=sender_id, now=timestamp, kind=kind, recipient=recipient_id)
    recipient_status = {
        'pending': 'm.canceled_at IS NULL AND m.due_at>:now',
        'sent': 'm.canceled_at IS NULL AND m.due_at<=:now',
        'canceled': 'm.canceled_at IS NOT NULL',
    }[status]
    compare, order = ('>', 'ASC') if status == 'pending' else ('<', 'DESC')
    boundary = ''
    if boundary_due is not None and boundary_group_id is not None:
        params['due'] = boundary_due
        params['group_id'] = boundary_group_id
        boundary = f'AND (due_at, group_id) {compare} (:due, :group_id)'
    return db.execute(
        f'''
        WITH grouped AS (
            {_AGGREGATE} AND (:kind IS NULL OR m.kind=:kind)
            GROUP BY group_id HAVING :recipient IS NULL OR max(m.recipient_id=:recipient AND {recipient_status})=1
        ) SELECT * FROM grouped WHERE {status}>0 {boundary}
        ORDER BY due_at {order}, group_id {order} LIMIT 21
        ''',
        params,
    ).fetchall()


def _group_condition(is_batch: bool) -> str:
    return 'm.dispatch_id=:target' if is_batch else 'm.id=:target AND m.dispatch_id IS NULL'


def get_dispatch_group_summary(db: sqlite3.Connection, sender_id: int, timestamp: int, is_batch: bool, target: int):
    condition = _group_condition(is_batch)
    return db.execute(
        f'{_AGGREGATE} AND {condition} GROUP BY group_id',
        dict(sender=sender_id, now=timestamp, target=target),
    ).fetchone()


def list_dispatch_recipients(db: sqlite3.Connection, sender_id: int, is_batch: bool, target: int):
    condition = _group_condition(is_batch)
    return db.execute(
        f'''
        SELECT m.id AS message_id, u.id, u.username, m.read_at, m.canceled_at
        FROM messages m JOIN users u ON m.recipient_id=u.id
        WHERE m.sender_id=:sender AND {condition} ORDER BY u.username COLLATE NOCASE, u.id
        ''',
        dict(sender=sender_id, target=target),
    ).fetchall()


def cancel_dispatch_group(db: sqlite3.Connection, sender_id: int, timestamp: int, is_batch: bool, target: int) -> None:
    condition = _group_condition(is_batch)
    db.execute(
        f'''
        UPDATE messages AS m SET canceled_at=:now WHERE m.sender_id=:sender AND {condition}
        AND m.due_at>:now AND m.canceled_at IS NULL
        ''',
        dict(sender=sender_id, target=target, now=timestamp),
    )
