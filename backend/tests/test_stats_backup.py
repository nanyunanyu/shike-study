from datetime import datetime

from fastapi.testclient import TestClient

from tests.conftest import bootstrap_users, login, make_client


def test_v1_backup_compatibility_and_v2_roundtrip(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}

        v2 = client.get('/api/backup').json()
        assert v2['version'] == 2

        v1 = {
            'version': 1,
            'preferences': {
                'focus_minutes': 30,
                'break_minutes': 5,
                'countdown_minutes': 45,
                'auto_break': True,
                'appearance': 'dark',
                'palette': 'mint',
            },
            'categories': v2['categories'],
            'plans': v2['plans'],
            'days': [
                {
                    'date': '2026-11-24',
                    'tasks': [dict(v2['plans'][0]['tasks'][0], done=True, override=None)],
                    'review': {
                        'effective': ['旧版有效记录'],
                        'issues': [],
                        'other': '',
                        'priorities': ['旧版计划'],
                        'adjustment': '',
                    },
                    'checked_at': int(datetime.fromisoformat('2026-11-24T20:00:00+08:00').timestamp()),
                }
            ],
            'focus': [],
        }

        prev = client.post('/api/backup/preview', headers=headers, json=v1)
        assert prev.status_code == 200, prev.text
        token = prev.json()['token']

        # Wrong preview token rejected
        assert client.put('/api/backup', headers=headers, json={'token': '0' * 64, 'backup': v1}).status_code == 409

        # Active timer blocks backup import
        client.post('/api/timer/start', headers=headers, json={'id': 'blk-1', 'date': '2026-11-25', 'mode': 'stopwatch'})
        assert client.put('/api/backup', headers=headers, json={'token': token, 'backup': v1}).status_code == 409
        client.post('/api/timer/action', headers=headers, json={'id': 'blk-1', 'revision': 0, 'action': 'finish'})

        commit = client.put('/api/backup', headers=headers, json={'token': token, 'backup': v1})
        assert commit.status_code == 200, commit.text
        assert commit.json()['preferences']['daily_focus_goal_minutes'] == 180
        assert commit.json()['preferences']['palette'] == 'mint'
        assert list((tmp_path / 'rollback').glob('*.json'))

        restored_day = client.get('/api/days/2026-11-24').json()
        assert restored_day['review']['effective'] == ['旧版有效记录']
        assert restored_day['review']['mood'] is None


def test_statistics_custom_date_range(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}
        today = '2026-11-25'

        res = client.post(
            '/api/timer/start',
            headers=headers,
            json={'id': 'range-run-1', 'date': today, 'mode': 'pomodoro', 'minutes': 20},
        )
        assert res.status_code == 200
        clock.advance(1200)
        assert client.get('/api/timer').status_code == 200

        custom = client.get('/api/statistics?start=2026-11-20&end=2026-11-25')
        assert custom.status_code == 200, custom.text
        body = custom.json()
        assert body['custom_range']['start'] == '2026-11-20'
        assert body['custom_range']['end'] == '2026-11-25'
        assert len(body['custom_range']['days']) == 6
        assert body['custom_range']['days'][-1]['seconds'] == 1200
        assert body['custom_range']['has_previous'] is False

        past = client.get('/api/statistics?start=2026-11-10&end=2026-11-15')
        assert past.status_code == 200
        assert len(past.json()['custom_range']['days']) == 6
        assert past.json()['categories'] == []

        assert client.get('/api/statistics?start=2026-11-20').status_code == 422
        assert client.get('/api/statistics?start=2026-11-25&end=2026-11-20').status_code == 422
        assert client.get('/api/statistics?start=2026-11-20&end=2026-11-28').status_code == 422
