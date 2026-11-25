import sqlite3


def get(db: sqlite3.Connection, uid: int, day: str):
    return db.execute('SELECT * FROM days WHERE user_id=? AND date=?', (uid, day)).fetchone()


def insert_ignore(db: sqlite3.Connection, uid: int, day: str, tasks_json: str, review_json: str) -> None:
    db.execute('INSERT OR IGNORE INTO days VALUES (?,?,?,?,NULL)', (uid, day, tasks_json, review_json))


def upsert_full(
    db: sqlite3.Connection,
    uid: int,
    day: str,
    tasks_json: str,
    review_json: str,
    checked_at: int | None,
) -> None:
    db.execute('INSERT OR REPLACE INTO days VALUES (?,?,?,?,?)', (uid, day, tasks_json, review_json, checked_at))


def update_tasks(db: sqlite3.Connection, uid: int, day: str, tasks_json: str) -> None:
    db.execute('UPDATE days SET tasks=? WHERE user_id=? AND date=?', (tasks_json, uid, day))


def update_review(db: sqlite3.Connection, uid: int, day: str, review_json: str) -> None:
    db.execute('UPDATE days SET review=? WHERE user_id=? AND date=?', (review_json, uid, day))


def set_checked_at_if_null(db: sqlite3.Connection, uid: int, day: str, timestamp: int) -> None:
    db.execute('UPDATE days SET checked_at=COALESCE(checked_at,?) WHERE user_id=? AND date=?', (timestamp, uid, day))


def clear_checked_at(db: sqlite3.Connection, uid: int, day: str) -> None:
    db.execute('UPDATE days SET checked_at=NULL WHERE user_id=? AND date=?', (uid, day))


def list_up_to(db: sqlite3.Connection, uid: int, today: str, *, descending: bool = False):
    order = 'DESC' if descending else 'ASC'
    return db.execute(f'SELECT * FROM days WHERE user_id=? AND date<=? ORDER BY date {order}', (uid, today)).fetchall()


def list_all(db: sqlite3.Connection, uid: int):
    return db.execute('SELECT * FROM days WHERE user_id=? ORDER BY date', (uid,)).fetchall()


def count_active_checkins_by_date(db: sqlite3.Connection, start_date: str, end_date: str) -> dict[str, int]:
    return dict(
        db.execute(
            '''
            SELECT d.date, count(*) FROM days d JOIN users u ON d.user_id=u.id
            WHERE d.date BETWEEN ? AND ? AND d.checked_at IS NOT NULL AND u.role='user' AND u.active=1
            GROUP BY d.date
            ''',
            (start_date, end_date),
        )
    )


def replace_all(db: sqlite3.Connection, uid: int, rows) -> None:
    db.execute('DELETE FROM days WHERE user_id=?', (uid,))
    db.executemany('INSERT INTO days VALUES (?,?,?,?,?)', rows)
