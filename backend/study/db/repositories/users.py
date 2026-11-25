import json
import sqlite3


def has_admin(db: sqlite3.Connection) -> bool:
    return db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone() is not None


def get_by_id(db: sqlite3.Connection, uid: int):
    return db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()


def get_by_username(db: sqlite3.Connection, username: str):
    return db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()


def get_preferences(db: sqlite3.Connection, uid: int):
    return db.execute('SELECT preferences FROM users WHERE id=?', (uid,)).fetchone()


def list_all(db: sqlite3.Connection):
    return db.execute('SELECT * FROM users ORDER BY id').fetchall()


def list_with_last_checkin(db: sqlite3.Connection, today: str):
    return db.execute(
        '''
        SELECT u.id, u.username, u.role, u.active, u.must_change,
            (SELECT max(date) FROM days WHERE user_id=u.id AND date<=? AND checked_at IS NOT NULL) AS last_checkin_date
        FROM users u ORDER BY u.id
        ''',
        (today,),
    ).fetchall()


def count_active_students(db: sqlite3.Connection) -> int:
    return db.execute("SELECT count(*) FROM users WHERE role='user' AND active=1").fetchone()[0]


def count_valid_active_recipients(db: sqlite3.Connection, recipient_ids: list[int]) -> int:
    return db.execute(
        '''
        SELECT count(*) FROM json_each(?) selected JOIN users u ON u.id=selected.value
        WHERE u.role='user' AND u.active=1
        ''',
        (json.dumps(recipient_ids),),
    ).fetchone()[0]


def insert(
    db: sqlite3.Connection,
    *,
    username: str,
    password_hash: str,
    role: str,
    must_change: bool,
    preferences_json: str,
    categories_json: str,
) -> int:
    cursor = db.execute(
        'INSERT INTO users(username,password,role,must_change,preferences,categories) VALUES (?,?,?,?,?,?)',
        (username, password_hash, role, must_change, preferences_json, categories_json),
    )
    return cursor.lastrowid


def update_login_failures(db: sqlite3.Connection, uid: int, failures: int, lock_until: int) -> None:
    db.execute('UPDATE users SET failures=?,lock_until=? WHERE id=?', (failures, lock_until, uid))


def reset_login_failures(db: sqlite3.Connection, uid: int) -> None:
    db.execute('UPDATE users SET failures=0,lock_until=0 WHERE id=?', (uid,))


def update_password(
    db: sqlite3.Connection,
    uid: int,
    password_hash: str,
    *,
    must_change: bool,
    reset_lock: bool = False,
) -> None:
    if reset_lock:
        db.execute(
            'UPDATE users SET password=?,must_change=?,failures=0,lock_until=0 WHERE id=?',
            (password_hash, must_change, uid),
        )
    else:
        db.execute('UPDATE users SET password=?,must_change=? WHERE id=?', (password_hash, int(must_change), uid))


def update_active(db: sqlite3.Connection, uid: int, active: bool) -> None:
    db.execute('UPDATE users SET active=? WHERE id=?', (active, uid))


def update_preferences(db: sqlite3.Connection, uid: int, preferences_json: str) -> None:
    db.execute('UPDATE users SET preferences=? WHERE id=?', (preferences_json, uid))


def update_categories(db: sqlite3.Connection, uid: int, categories_json: str) -> None:
    db.execute('UPDATE users SET categories=? WHERE id=?', (categories_json, uid))


def update_preferences_and_categories(
    db: sqlite3.Connection, uid: int, preferences_json: str, categories_json: str
) -> None:
    db.execute('UPDATE users SET preferences=?,categories=? WHERE id=?', (preferences_json, categories_json, uid))


def delete(db: sqlite3.Connection, uid: int) -> None:
    db.execute('DELETE FROM users WHERE id=?', (uid,))
