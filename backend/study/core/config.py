import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
COOKIE_NAME = 'study_session'
SESSION_AGE = 7 * 86400
MAX_BODY_BYTES = 16 * 1024 * 1024
MAX_SAFE_ID = 2**53 - 1
LOCKOUT_THRESHOLD = 5
LOCKOUT_SECONDS = 900
MAINTENANCE_INTERVAL = 15
SNAPSHOT_RETENTION = 30
DEFAULT_ALLOWED_HOSTS = ('127.0.0.1', 'localhost', '[::1]', 'testserver')


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    data_dir: Path
    timezone: str
    allowed_hosts: tuple[str, ...]
    public_origins: frozenset[str]
    cookie_name: str = COOKIE_NAME
    session_age: int = SESSION_AGE
    max_body_bytes: int = MAX_BODY_BYTES
    maintenance_interval: int = MAINTENANCE_INTERVAL

    @classmethod
    def from_env(cls, directory=None) -> 'Settings':
        data_dir = Path(directory or os.environ.get('STUDY_DATA_DIR') or BACKEND_ROOT / 'data')
        extra_hosts = [
            item.strip()
            for item in os.environ.get('STUDY_ALLOWED_HOSTS', '').split(',')
            if item.strip()
        ]
        public_origins = frozenset(
            item.strip().lower()
            for item in os.environ.get('STUDY_ALLOWED_ORIGINS', '').split(',')
            if item.strip()
        )
        return cls(
            root_dir=BACKEND_ROOT,
            data_dir=data_dir,
            timezone=os.environ.get('STUDY_TIMEZONE', 'Asia/Shanghai'),
            allowed_hosts=(*DEFAULT_ALLOWED_HOSTS, *extra_hosts),
            public_origins=public_origins,
        )

    def frontend_dist(self) -> Path:
        frontend_dir = self.root_dir.parent / 'frontend'
        candidates = (
            frontend_dir / 'webui',
            frontend_dir / 'dist',
            self.root_dir / 'webui',
            self.root_dir / 'dist',
        )
        return next((candidate for candidate in candidates if (candidate / 'index.html').is_file()), frontend_dir / 'webui')
