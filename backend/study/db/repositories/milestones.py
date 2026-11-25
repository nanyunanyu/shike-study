import sqlite3


def list_ordered(db: sqlite3.Connection, uid: int):
    return db.execute(
        '''
        SELECT * FROM milestones WHERE user_id=?
        ORDER BY completed ASC, pinned DESC, target_date ASC, created_at DESC
        ''',
        (uid,),
    ).fetchall()


def list_all(db: sqlite3.Connection, uid: int):
    return db.execute('SELECT * FROM milestones WHERE user_id=? ORDER BY created_at, id', (uid,)).fetchall()


def count(db: sqlite3.Connection, uid: int) -> int:
    return db.execute('SELECT count(*) FROM milestones WHERE user_id=?', (uid,)).fetchone()[0]


def get(db: sqlite3.Connection, uid: int, milestone_id: str):
    return db.execute('SELECT * FROM milestones WHERE user_id=? AND id=?', (uid, milestone_id)).fetchone()


def insert(
    db: sqlite3.Connection,
    uid: int,
    milestone_id: str,
    title: str,
    target_date: str,
    note: str,
    color: str,
    pinned: int,
    completed: int,
    created_at: int,
) -> None:
    db.execute(
        '''
        INSERT INTO milestones (user_id,id,title,target_date,note,color,pinned,completed,created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        ''',
        (uid, milestone_id, title, target_date, note, color, pinned, completed, created_at),
    )


def update(
    db: sqlite3.Connection,
    uid: int,
    milestone_id: str,
    title: str,
    target_date: str,
    note: str,
    color: str,
    pinned: int,
    completed: int,
) -> int:
    result = db.execute(
        '''
        UPDATE milestones
        SET title=?, target_date=?, note=?, color=?, pinned=?, completed=?
        WHERE user_id=? AND id=?
        ''',
        (title, target_date, note, color, pinned, completed, uid, milestone_id),
    )
    return result.rowcount


def delete(db: sqlite3.Connection, uid: int, milestone_id: str) -> int:
    return db.execute('DELETE FROM milestones WHERE user_id=? AND id=?', (uid, milestone_id)).rowcount


def replace_all(db: sqlite3.Connection, uid: int, rows) -> None:
    db.execute('DELETE FROM milestones WHERE user_id=?', (uid,))
    rows_list = list(rows)
    if rows_list:
        db.executemany('INSERT INTO milestones VALUES (?,?,?,?,?,?,?,?,?)', rows_list)
