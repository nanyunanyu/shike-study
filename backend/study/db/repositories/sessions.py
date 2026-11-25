import sqlite3


def get_active_user_session(db: sqlite3.Connection, token_hash: str, now: int):
    return db.execute(
        'SELECT users.*,sessions.csrf,sessions.token_hash FROM sessions JOIN users '
        'ON users.id=sessions.user_id WHERE token_hash=? AND expires>? AND active=1',
        (token_hash, now),
    ).fetchone()


def insert(db: sqlite3.Connection, token_hash: str, user_id: int, csrf: str, expires: int) -> None:
    db.execute('INSERT INTO sessions VALUES (?,?,?,?)', (token_hash, user_id, csrf, expires))


def delete_by_token(db: sqlite3.Connection, token_hash: str) -> None:
    db.execute('DELETE FROM sessions WHERE token_hash=?', (token_hash,))


def delete_by_token_and_user(db: sqlite3.Connection, token_hash: str, user_id: int) -> None:
    db.execute('DELETE FROM sessions WHERE token_hash=? AND user_id=?', (token_hash, user_id))


def delete_other_sessions(db: sqlite3.Connection, user_id: int, keep_token_hash: str) -> None:
    db.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?', (user_id, keep_token_hash))


def delete_all_for_user(db: sqlite3.Connection, user_id: int) -> None:
    db.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))


def purge_expired(db: sqlite3.Connection, now: int) -> None:
    db.execute('DELETE FROM sessions WHERE expires<=?', (now,))
