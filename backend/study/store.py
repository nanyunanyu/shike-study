import json
import os
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from .models import Preferences, Review
from .seed import BUILTINS, default_tasks

HASHER = PasswordHasher()


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def key():
    return uuid4().hex


def make_dir(path, mode=0o700):
    try:
        Path(path).mkdir(parents=True, mode=mode, exist_ok=True)
    except FileExistsError:
        pass


def verify(password_hash, password):
    try:
        return HASHER.verify(password_hash, password)
    except VerificationError:
        return False


def normalize_preferences(raw):
    base = Preferences().model_dump()
    if isinstance(raw, dict):
        for field in base:
            if field in raw:
                base[field] = raw[field]
    return base


def normalize_review(raw):
    base = Review().model_dump()
    if isinstance(raw, dict):
        for field in base:
            if field in raw:
                base[field] = raw[field]
    return base


def normalize_task(item):
    result = dict(item)
    result.setdefault('done', False)
    result.setdefault('override', None)
    result.setdefault('adhoc', False)
    return result


def insert_adhoc_task(tasks, item):
    target_start = (item.get('override') or item)['start']
    result = list(tasks)
    insert_at = len(result)
    for index, existing in enumerate(result):
        existing_start = (existing.get('override') or existing)['start']
        if existing_start > target_start:
            insert_at = index
            break
    result.insert(insert_at, item)
    return result


class Store:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.path = self.directory / 'study.sqlite3'
        self.zone = None

    def connect(self):
        db = sqlite3.connect(self.path, timeout=8, isolation_level=None, check_same_thread=False)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        return db

    def initialize(self, timezone):
        make_dir(self.directory)
        with self.transaction() as db:
            db.execute('PRAGMA journal_mode = WAL')
            db.execute('BEGIN IMMEDIATE')
            version = db.execute('PRAGMA user_version').fetchone()[0]
            migrations = sorted(Path(__file__).with_name('migrations').glob('*.sql'))
            if version > len(migrations):
                raise RuntimeError('数据库版本比应用新')
            for migration in migrations[version:]:
                for statement in migration.read_text().split(';'):
                    if statement.strip():
                        db.execute(statement)
                version += 1
                db.execute(f'PRAGMA user_version = {version}')
            settings = db.execute("SELECT value FROM metadata WHERE key='timezone'").fetchone()
            self.zone = ZoneInfo(settings[0] if settings else timezone)
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('timezone',?)", (self.zone.key,))
        self.path.chmod(0o600)

    @contextmanager
    def transaction(self, write=False, *, read=False):
        db = self.connect()
        try:
            if write or read:
                db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def date(self, timestamp):
        return datetime.fromtimestamp(timestamp, self.zone).date()

    def write_private(self, folder, name, content):
        folder = self.directory / folder
        make_dir(folder)
        tmp = folder / f'.{key()}.tmp'
        try:
            with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            tmp.replace(folder / name)
        finally:
            tmp.unlink(missing_ok=True)

    def snapshot(self, timestamp):
        folder = self.directory / 'snapshots'
        make_dir(folder)
        target = folder / f'{self.date(timestamp)}.sqlite3'
        if target.exists():
            return
        temp = folder / f'.{key()}.tmp'
        try:
            temp.touch(mode=0o600, exist_ok=False)
            with self.transaction() as source, closing(sqlite3.connect(temp)) as destination:
                source.backup(destination)
                destination.execute('PRAGMA journal_mode = DELETE')
            temp.replace(target)
        finally:
            temp.unlink(missing_ok=True)
        for old in sorted(folder.glob('????-??-??.sqlite3'), reverse=True)[30:]:
            old.unlink(missing_ok=True)


def create_user(db, *, username, password, role, must_change, today, now):
    cursor = db.execute(
        'INSERT INTO users(username,password,role,must_change,preferences,categories) VALUES (?,?,?,?,?,?)',
        (username, HASHER.hash(password), role, must_change, encode(Preferences().model_dump()), encode(BUILTINS)),
    )
    user_id = cursor.lastrowid
    db.execute('INSERT INTO plans VALUES (?,?,?,?,?)', (user_id, key(), today, now, encode(default_tasks())))
    return user_id


def plan_row(db, uid, today):
    return db.execute(
        'SELECT * FROM plans WHERE user_id=? AND date<=? ORDER BY date DESC, created_at DESC, rowid DESC LIMIT 1',
        (uid, today),
    ).fetchone()


def unpack_plan(row):
    return dict(id=row['id'], date=row['date'], created_at=row['created_at'], tasks=json.loads(row['tasks']))


def day_tasks(tasks, previous=()):
    old = {item['id']: item for item in previous}
    merged = [
        dict(
            item,
            done=old.get(item['id'], {}).get('done', False),
            override=old.get(item['id'], {}).get('override'),
            adhoc=False,
        )
        for item in tasks
    ]
    plan_ids = {item['id'] for item in merged}
    for item in previous:
        if item.get('adhoc') and item['id'] not in plan_ids:
            merged = insert_adhoc_task(merged, normalize_task(item))
    return merged


def create_day(db, uid, day):
    plan = plan_row(db, uid, day)
    tasks = day_tasks(json.loads(plan['tasks'])) if plan else []
    db.execute(
        'INSERT OR IGNORE INTO days VALUES (?,?,?,?,NULL)',
        (uid, day, encode(tasks), encode(Review().model_dump())),
    )


def day_row(db, uid, day):
    return db.execute('SELECT * FROM days WHERE user_id=? AND date=?', (uid, day)).fetchone()


def unpack_focus(row):
    return {
        k: json.loads(row[k]) if k == 'task' and row[k] else row[k]
        for k in ('id', 'date', 'started_at', 'ended_at', 'seconds', 'mode', 'task')
    }


def get_day(db, uid, day, today, *, editable=True):
    row = day_row(db, uid, day)
    focus = []
    if row:
        tasks = [normalize_task(t) for t in json.loads(row['tasks'])]
        review = normalize_review(json.loads(row['review']))
        focus = [
            unpack_focus(s)
            for s in db.execute(
                'SELECT * FROM focus WHERE user_id=? AND date=? ORDER BY started_at DESC,id', (uid, day)
            )
        ]
    else:
        plan = plan_row(db, uid, day) if day == today else None
        tasks = day_tasks(json.loads(plan['tasks'])) if plan else []
        review = Review().model_dump()
    return dict(
        date=day,
        today=today,
        exists=bool(row),
        editable=editable and day == today,
        tasks=tasks,
        review=review,
        checked_at=row['checked_at'] if row else None,
        focus=focus,
        focus_seconds=sum(s['seconds'] for s in focus),
    )
