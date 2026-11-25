import sqlite3


def get_state_json(db: sqlite3.Connection, uid: int) -> str | None:
    row = db.execute('SELECT state FROM timers WHERE user_id=?', (uid,)).fetchone()
    return row[0] if row else None


def list_all(db: sqlite3.Connection):
    return db.execute('SELECT user_id,state FROM timers').fetchall()


def upsert_state_json(db: sqlite3.Connection, uid: int, state_json: str) -> None:
    db.execute(
        'INSERT INTO timers VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET state=excluded.state',
        (uid, state_json),
    )


def delete_state(db: sqlite3.Connection, uid: int) -> None:
    db.execute('DELETE FROM timers WHERE user_id=?', (uid,))


def insert_request(db: sqlite3.Connection, uid: int, request_id: str, day: str) -> None:
    db.execute('INSERT INTO timer_requests VALUES (?,?,?)', (uid, request_id, day))


def purge_old_requests(db: sqlite3.Connection, before_date: str) -> None:
    db.execute('DELETE FROM timer_requests WHERE date<?', (before_date,))
