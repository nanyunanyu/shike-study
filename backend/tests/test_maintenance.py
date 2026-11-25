from fastapi.testclient import TestClient

from study.bootstrap import prepare
from study.db.connection import Store
from study.services.demo import seed_demo_data
from study.services.maintenance import run_maintenance
from tests.conftest import bootstrap_users, login, make_client


def test_maintenance_settles_timers_and_writes_snapshot(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        client.post(
            '/api/timer/start',
            headers={'X-CSRF-Token': csrf},
            json={'id': 'maint-1', 'date': '2026-11-25', 'mode': 'countdown', 'minutes': 10},
        )
        clock.advance(600)
        run_maintenance(app.state.store, clock())

        day = client.get('/api/days/2026-11-25').json()
        assert day['focus_seconds'] == 600
        assert (tmp_path / 'snapshots' / '2026-11-25.sqlite3').is_file()


def test_bootstrap_prepare_and_seed_demo_idempotency(tmp_path, monkeypatch):
    monkeypatch.setenv('STUDY_ADMIN_USERNAME', 'rootadmin')
    monkeypatch.setenv('STUDY_ADMIN_PASSWORD', 'Secret123')
    monkeypatch.setenv('STUDY_MEMBER_USERNAME', 'student1')
    monkeypatch.setenv('STUDY_MEMBER_PASSWORD', 'Secret123')

    boot_dir = tmp_path / 'boot'
    assert prepare(boot_dir) == boot_dir
    # Idempotent on second run
    assert prepare(boot_dir) == boot_dir

    # Demo seeding creates accounts once and skips on repeat
    demo_dir = tmp_path / 'demo'
    store = Store(demo_dir)
    store.initialize('Asia/Shanghai')
    assert seed_demo_data(store) is True
    assert seed_demo_data(store) is False
