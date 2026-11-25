from fastapi.testclient import TestClient

from tests.conftest import bootstrap_users, login, make_client


def test_milestones_reviews_timer_and_achievements(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}
        today = '2026-11-25'

        res = client.post(
            '/api/milestones',
            headers=headers,
            json={'title': '期末答辩', 'target_date': '2026-12-25', 'note': '冲刺准备', 'color': 'blue', 'pinned': True},
        )
        assert res.status_code == 201
        ms = res.json()
        assert ms['days_left'] == 30
        assert ms['pinned'] is True

        res = client.put(
            f"/api/milestones/{ms['id']}",
            headers=headers,
            json={'title': '期末答辩（终版）', 'target_date': '2026-12-20', 'note': '冲刺', 'color': 'mint', 'pinned': True, 'completed': False},
        )
        assert res.status_code == 200
        assert res.json()['days_left'] == 25

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

        res = client.get('/api/reviews?mood=great&q=白噪音')
        assert res.status_code == 200
        timeline = res.json()
        assert timeline['summary']['total_reviews'] == 1
        assert timeline['summary']['avg_focus_score'] == 5.0
        assert len(timeline['items']) == 1
        assert timeline['items'][0]['date'] == today

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

        stats = client.get('/api/statistics').json()
        assert stats['streak'] == 1
        assert stats['today_focus_seconds'] == 900
        assert stats['reviews_count'] == 1
        assert len(stats['pinned_milestones']) == 1
        assert len(stats['achievements']) == 15
        unlocked_ids = {a['id'] for a in stats['achievements'] if a['unlocked']}
        assert 'first_checkin' in unlocked_ids

        res = client.delete(f"/api/milestones/{ms['id']}", headers=headers)
        assert res.status_code == 200
        assert client.get('/api/milestones').json() == []
        assert client.delete(f"/api/milestones/{ms['id']}", headers=headers).status_code == 404
