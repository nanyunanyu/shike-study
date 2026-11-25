import sqlite3


def get_effective(db: sqlite3.Connection, uid: int, on_date: str):
    return db.execute(
        'SELECT * FROM plans WHERE user_id=? AND date<=? ORDER BY date DESC, created_at DESC, rowid DESC LIMIT 1',
        (uid, on_date),
    ).fetchone()


def get_by_id(db: sqlite3.Connection, uid: int, plan_id: str):
    return db.execute('SELECT * FROM plans WHERE user_id=? AND id=?', (uid, plan_id)).fetchone()


def list_history(db: sqlite3.Connection, uid: int):
    return db.execute(
        'SELECT id,date,created_at FROM plans WHERE user_id=? ORDER BY date DESC,created_at DESC,rowid DESC',
        (uid,),
    ).fetchall()


def list_all(db: sqlite3.Connection, uid: int):
    return db.execute('SELECT * FROM plans WHERE user_id=? ORDER BY date,created_at,rowid', (uid,)).fetchall()


def insert(
    db: sqlite3.Connection,
    uid: int,
    plan_id: str,
    on_date: str,
    created_at: int,
    tasks_json: str,
) -> None:
    db.execute('INSERT INTO plans VALUES (?,?,?,?,?)', (uid, plan_id, on_date, created_at, tasks_json))


def replace_all(db: sqlite3.Connection, uid: int, rows) -> None:
    db.execute('DELETE FROM plans WHERE user_id=?', (uid,))
    db.executemany('INSERT INTO plans VALUES (?,?,?,?,?)', rows)
