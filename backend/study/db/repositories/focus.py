import sqlite3


def list_by_day(db: sqlite3.Connection, uid: int, day: str):
    return db.execute(
        'SELECT * FROM focus WHERE user_id=? AND date=? ORDER BY started_at DESC,id',
        (uid, day),
    ).fetchall()


def list_up_to(db: sqlite3.Connection, uid: int, today: str):
    return db.execute(
        'SELECT * FROM focus WHERE user_id=? AND date<=? ORDER BY date,ended_at',
        (uid, today),
    ).fetchall()


def list_all(db: sqlite3.Connection, uid: int):
    return db.execute('SELECT * FROM focus WHERE user_id=? ORDER BY started_at,id', (uid,)).fetchall()


def sum_by_date_up_to(db: sqlite3.Connection, uid: int, today: str) -> dict[str, int]:
    return dict(
        db.execute(
            'SELECT date, sum(seconds) FROM focus WHERE user_id=? AND date<=? GROUP BY date',
            (uid, today),
        )
    )


def sum_active_users_by_date(db: sqlite3.Connection, start_date: str, end_date: str) -> dict[str, int]:
    return dict(
        db.execute(
            '''
            SELECT f.date, sum(f.seconds) FROM focus f JOIN users u ON f.user_id=u.id
            WHERE f.date BETWEEN ? AND ? AND u.role='user' AND u.active=1 GROUP BY f.date
            ''',
            (start_date, end_date),
        )
    )


def insert_ignore(
    db: sqlite3.Connection,
    uid: int,
    focus_id: str,
    day: str,
    started_at: int,
    ended_at: int,
    seconds: int,
    mode: str,
    task_json: str | None,
) -> None:
    db.execute(
        'INSERT OR IGNORE INTO focus VALUES (?,?,?,?,?,?,?,?)',
        (uid, focus_id, day, started_at, ended_at, seconds, mode, task_json),
    )


def insert_many(db: sqlite3.Connection, rows) -> None:
    db.executemany('INSERT INTO focus VALUES (?,?,?,?,?,?,?,?)', rows)


def exists_request_or_focus(db: sqlite3.Connection, uid: int, request_id: str) -> bool:
    return (
        db.execute(
            'SELECT 1 FROM timer_requests WHERE user_id=? AND id=? '
            'UNION ALL SELECT 1 FROM focus WHERE user_id=? AND id=?',
            (uid, request_id, uid, request_id),
        ).fetchone()
        is not None
    )
