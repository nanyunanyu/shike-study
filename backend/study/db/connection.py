import os
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..core.config import SNAPSHOT_RETENTION
from ..core.security import new_key


def make_dir(path, mode=0o700) -> None:
    try:
        Path(path).mkdir(parents=True, mode=mode, exist_ok=True)
    except FileExistsError:
        pass


class Store:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.path = self.directory / 'study.sqlite3'
        self.zone: ZoneInfo | None = None

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=8, isolation_level=None, check_same_thread=False)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        return db

    def initialize(self, timezone: str) -> None:
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
    def transaction(self, write: bool = False, *, read: bool = False):
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

    def date(self, timestamp: int):
        return datetime.fromtimestamp(timestamp, self.zone).date()

    def write_private(self, folder: str, name: str, content: bytes) -> None:
        target_dir = self.directory / folder
        make_dir(target_dir)
        tmp = target_dir / f'.{new_key()}.tmp'
        try:
            with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            tmp.replace(target_dir / name)
        finally:
            tmp.unlink(missing_ok=True)

    def snapshot(self, timestamp: int) -> None:
        folder = self.directory / 'snapshots'
        make_dir(folder)
        target = folder / f'{self.date(timestamp)}.sqlite3'
        if target.exists():
            return
        temp = folder / f'.{new_key()}.tmp'
        try:
            temp.touch(mode=0o600, exist_ok=False)
            with self.transaction() as source, closing(sqlite3.connect(temp)) as destination:
                source.backup(destination)
                destination.execute('PRAGMA journal_mode = DELETE')
            temp.replace(target)
        finally:
            temp.unlink(missing_ok=True)
        for old in sorted(folder.glob('????-??-??.sqlite3'), reverse=True)[SNAPSHOT_RETENTION:]:
            old.unlink(missing_ok=True)
