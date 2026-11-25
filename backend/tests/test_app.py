import json
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from study.main import create_app
from study.store import create_user


class Clock:
    def __init__(self, iso='2026-11-25T10:00:00+08:00'):
        self.current = int(datetime.fromisoformat(iso).timestamp())

    def __call__(self):
        return self.current

    def advance(self, seconds: int):
        self.current += seconds


def make_client(tmp_path, clock=None):
    clock = clock or Clock()
    app = create_app(tmp_path, clock=clock)
    return app, clock


def bootstrap_users(app, clock):
    store = app.state.store
    store.initialize('Asia/Shanghai')
    today = store.date(clock()).isoformat()
    with store.transaction(write=True) as db:
        create_user(db, username='admin', password='Password123', role='admin', must_change=False, today=today, now=clock())
        create_user(db, username='alice', password='Password123', role='user', must_change=False, today=today, now=clock())


def login(client: TestClient, username: str, password: str = 'Password123'):
    res = client.post('/api/auth/login', json={'username': username, 'password': password})
    assert res.status_code == 200, res.text
    return res.json()['csrf']


def test_adhoc_tasks_crud_and_plan_preservation(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}
        today = '2026-11-25'

        # Add ad-hoc task
        res = client.post(
            f'/api/days/{today}/tasks',
            headers=headers,
            json={'title': '临时刷真题', 'start': '10:30', 'end': '11:00', 'category': 'practice', 'note': '2024卷', 'estimate': 30},
        )
        assert res.status_code == 201, res.text
        day = res.json()
        adhoc = [t for t in day['tasks'] if t.get('adhoc')]
        assert len(adhoc) == 1
        assert adhoc[0]['title'] == '临时刷真题'
        adhoc_id = adhoc[0]['id']

        # Edit ad-hoc task
        res = client.put(
            f'/api/days/{today}/tasks/{adhoc_id}',
            headers=headers,
            json={'title': '临时刷真题（更新）', 'start': '10:40', 'end': '11:15', 'category': 'review', 'note': '含复盘', 'estimate': 35},
        )
        assert res.status_code == 200
        updated = next(t for t in res.json()['tasks'] if t['id'] == adhoc_id)
        assert updated['title'] == '临时刷真题（更新）'
        assert updated['category_name'] == '整理复盘'

        # Update master plan and verify today's ad-hoc task is preserved!
        plan = client.get('/api/plan').json()
        new_tasks = [
            {k: t[k] for k in ('id', 'title', 'start', 'end', 'category', 'note', 'estimate')}
            for t in plan['current']['tasks'][:3]
        ]
        res = client.put('/api/plan', headers=headers, json={'base': plan['current']['id'], 'tasks': new_tasks})
        assert res.status_code == 200
        day_after = client.get(f'/api/days/{today}').json()
        assert len(day_after['tasks']) == 4
        assert any(t['id'] == adhoc_id and t['adhoc'] for t in day_after['tasks'])

        # Cannot delete plan-derived task via ad-hoc endpoint
        plan_task_id = new_tasks[0]['id']
        res = client.delete(f'/api/days/{today}/tasks/{plan_task_id}', headers=headers)
        assert res.status_code == 409

        # Delete ad-hoc task succeeds
        res = client.delete(f'/api/days/{today}/tasks/{adhoc_id}', headers=headers)
        assert res.status_code == 200
        assert not any(t['id'] == adhoc_id for t in res.json()['tasks'])


def test_milestones_reviews_timer_and_achievements(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}
        today = '2026-11-25'

        # Create milestones
        res = client.post(
            '/api/milestones',
            headers=headers,
            json={'title': '期末答辩', 'target_date': '2026-12-25', 'note': '冲刺准备', 'color': 'blue', 'pinned': True},
        )
        assert res.status_code == 201
        ms = res.json()
        assert ms['days_left'] == 30
        assert ms['pinned'] is True

        # Update milestone
        res = client.put(
            f"/api/milestones/{ms['id']}",
            headers=headers,
            json={'title': '期末答辩（终版）', 'target_date': '2026-12-20', 'note': '冲刺', 'color': 'mint', 'pinned': True, 'completed': False},
        )
        assert res.status_code == 200
        assert res.json()['days_left'] == 25

        # Check-in & save upgraded review
        res = client.post(f'/api/days/{today}/check-in', headers=headers)
        assert res.status_code == 200
        assert res.json()['checked_at'] is not None

        review_payload = {
            'effective': ['吃透了动态规划状态转移'],
            'issues': ['走神'],
            'other': '',
            'priorities': ['刷完背包专题'],
            'adjustment': '手机放书桌外',
            'mood': 'great',
            'focus_score': 5,
            'reflection': '今天心流非常稳定，白噪音很有效。',
        }
        res = client.put(f'/api/days/{today}/review', headers=headers, json=review_payload)
        assert res.status_code == 200
        assert res.json()['review']['mood'] == 'great'
        assert res.json()['review']['focus_score'] == 5

        # Query review timeline with filters
        res = client.get('/api/reviews?mood=great&q=白噪音')
        assert res.status_code == 200
        timeline = res.json()
        assert timeline['summary']['total_reviews'] == 1
        assert timeline['summary']['avg_focus_score'] == 5.0
        assert len(timeline['items']) == 1
        assert timeline['items'][0]['date'] == today

        # Start pomodoro with custom preset minutes (15m), advance 15m -> settles into focus
        res = client.post(
            '/api/timer/start',
            headers=headers,
            json={'id': 'preset-run-1', 'date': today, 'mode': 'pomodoro', 'minutes': 15},
        )
        assert res.status_code == 200
        assert res.json()['timer']['duration'] == 900
        clock.advance(900)
        settled = client.get('/api/timer').json()
        assert settled['timer']['stage'] == 'offer'

        # Statistics & achievements
        stats = client.get('/api/statistics').json()
        assert stats['streak'] == 1
        assert stats['today_focus_seconds'] == 900
        assert stats['reviews_count'] == 1
        assert len(stats['pinned_milestones']) == 1
        assert len(stats['achievements']) == 15
        unlocked_ids = {a['id'] for a in stats['achievements'] if a['unlocked']}
        assert 'first_checkin' in unlocked_ids

        # Delete milestone
        res = client.delete(f"/api/milestones/{ms['id']}", headers=headers)
        assert res.status_code == 200
        assert client.get('/api/milestones').json() == []


def test_v1_backup_compatibility_and_v2_roundtrip(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}

        # Export v2, then synthesize a legacy v1 backup (without daily_focus_goal_minutes, mood, milestones)
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

        commit = client.put('/api/backup', headers=headers, json={'token': token, 'backup': v1})
        assert commit.status_code == 200, commit.text
        assert commit.json()['preferences']['daily_focus_goal_minutes'] == 180
        assert commit.json()['preferences']['palette'] == 'mint'

        restored_day = client.get('/api/days/2026-11-24').json()
        assert restored_day['review']['effective'] == ['旧版有效记录']
        assert restored_day['review']['mood'] is None


def test_admin_dispatches_and_inbox(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as admin_client, TestClient(app) as user_client:
        admin_csrf = login(admin_client, 'admin')
        user_csrf = login(user_client, 'alice')

        overview = admin_client.get('/api/admin/overview').json()
        alice_id = next(u['id'] for u in overview['accounts'] if u['username'] == 'alice')

        send_res = admin_client.post(
            '/api/admin/dispatches',
            headers={'X-CSRF-Token': admin_csrf},
            json={
                'request_id': 'a' * 32,
                'recipient_ids': [alice_id],
                'kind': 'encouragement',
                'body': '继续保持专注！',
                'scheduled_for': None,
                'all_active': False,
            },
        )
        assert send_res.status_code == 201, send_res.text

        status = user_client.get('/api/messages/status').json()
        assert status['unread'] == 1
        assert status['pending'] is True

        inbox = user_client.get('/api/messages').json()
        assert len(inbox['items']) == 1
        msg_id = inbox['items'][0]['id']

        read_res = user_client.put(f'/api/messages/{msg_id}/read', headers={'X-CSRF-Token': user_csrf})
        assert read_res.status_code == 200
        assert read_res.json()['read_at'] is not None


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

        # Past window excluding today
        past = client.get('/api/statistics?start=2026-11-10&end=2026-11-15')
        assert past.status_code == 200
        assert len(past.json()['custom_range']['days']) == 6
        assert past.json()['categories'] == []

        # Validation errors
        assert client.get('/api/statistics?start=2026-11-20').status_code == 422
        assert client.get('/api/statistics?start=2026-11-25&end=2026-11-20').status_code == 422
        assert client.get('/api/statistics?start=2026-11-20&end=2026-11-28').status_code == 422
