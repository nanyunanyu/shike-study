from datetime import datetime

from fastapi.testclient import TestClient

from study.main import create_app
from study.services.seed import create_user


class Clock:
    def __init__(self, iso: str = '2026-11-25T10:00:00+08:00'):
        self.current = int(datetime.fromisoformat(iso).timestamp())

    def __call__(self):
        return self.current

    def advance(self, seconds: int):
        self.current += seconds


def make_client(tmp_path, clock=None):
    clock = clock or Clock()
    app = create_app(tmp_path, clock=clock)
    return app, clock


def bootstrap_users(app, clock, *, alice_must_change: bool = False):
    store = app.state.store
    store.initialize('Asia/Shanghai')
    today = store.date(clock()).isoformat()
    with store.transaction(write=True) as db:
        create_user(
            db,
            username='admin',
            password='Password123',
            role='admin',
            must_change=False,
            today=today,
            now=clock(),
        )
        create_user(
            db,
            username='alice',
            password='Password123',
            role='user',
            must_change=alice_must_change,
            today=today,
            now=clock(),
        )


def login(client: TestClient, username: str, password: str = 'Password123') -> str:
    res = client.post('/api/auth/login', json={'username': username, 'password': password})
    assert res.status_code == 200, res.text
    return res.json()['csrf']
