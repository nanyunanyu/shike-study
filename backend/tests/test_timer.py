from fastapi.testclient import TestClient

from tests.conftest import bootstrap_users, login, make_client


def test_timer_modes_actions_idempotency_and_auto_break(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}
        today = '2026-11-25'

        # Start pomodoro with custom 15m preset
        res = client.post(
            '/api/timer/start',
            headers=headers,
            json={'id': 'run-1', 'date': today, 'mode': 'pomodoro', 'minutes': 15},
        )
        assert res.status_code == 200
        timer = res.json()['timer']
        assert timer['duration'] == 900

        # Duplicate start with same id is idempotent; different id conflicts (409)
        assert client.post('/api/timer/start', headers=headers, json={'id': 'run-1', 'date': today, 'mode': 'pomodoro'}).status_code == 200
        assert client.post('/api/timer/start', headers=headers, json={'id': 'run-2', 'date': today, 'mode': 'pomodoro'}).status_code == 409

        # Pause after 5m, advance 10m while paused, resume, finish remaining 10m -> offer stage
        clock.advance(300)
        paused = client.post('/api/timer/action', headers=headers, json={'id': 'run-1', 'revision': 0, 'action': 'pause'})
        assert paused.status_code == 200
        assert paused.json()['timer']['elapsed'] == 300
        assert paused.json()['timer']['running_since'] is None

        clock.advance(600)
        resumed = client.post('/api/timer/action', headers=headers, json={'id': 'run-1', 'revision': 1, 'action': 'resume'})
        assert resumed.status_code == 200
        assert resumed.json()['timer']['running_since'] == clock()

        clock.advance(600)
        offered = client.get('/api/timer').json()
        assert offered['timer']['stage'] == 'offer'

        # Start break and let break complete
        brk = client.post(
            '/api/timer/action',
            headers=headers,
            json={'id': 'run-1', 'revision': offered['timer']['revision'], 'action': 'start_break'},
        )
        assert brk.status_code == 200 and brk.json()['timer']['stage'] == 'break'
        clock.advance(300)
        assert client.get('/api/timer').json()['timer'] is None

        # Stopwatch manual finish records focus seconds
        sw = client.post('/api/timer/start', headers=headers, json={'id': 'sw-1', 'date': today, 'mode': 'stopwatch'})
        assert sw.status_code == 200 and sw.json()['timer']['duration'] is None
        clock.advance(120)
        fin = client.post('/api/timer/action', headers=headers, json={'id': 'sw-1', 'revision': 0, 'action': 'finish'})
        assert fin.status_code == 200 and fin.json()['timer'] is None

        day = client.get(f'/api/days/{today}').json()
        assert day['focus_seconds'] == 1020
