from fastapi.testclient import TestClient

from tests.conftest import bootstrap_users, login, make_client


def test_adhoc_tasks_crud_and_plan_preservation(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}
        today = '2026-11-25'

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

        res = client.put(
            f'/api/days/{today}/tasks/{adhoc_id}',
            headers=headers,
            json={'title': '临时刷真题（更新）', 'start': '10:40', 'end': '11:15', 'category': 'review', 'note': '含复盘', 'estimate': 35},
        )
        assert res.status_code == 200
        updated = next(t for t in res.json()['tasks'] if t['id'] == adhoc_id)
        assert updated['title'] == '临时刷真题（更新）'
        assert updated['category_name'] == '整理复盘'

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

        plan_task_id = new_tasks[0]['id']
        res = client.delete(f'/api/days/{today}/tasks/{plan_task_id}', headers=headers)
        assert res.status_code == 409

        res = client.delete(f'/api/days/{today}/tasks/{adhoc_id}', headers=headers)
        assert res.status_code == 200
        assert not any(t['id'] == adhoc_id for t in res.json()['tasks'])


def test_day_done_override_checkin_and_date_guards(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}
        today = '2026-11-25'

        # Future date -> 404; past date write -> 409
        assert client.get('/api/days/2026-11-26').status_code == 404
        assert client.post('/api/days/2026-11-24/check-in', headers=headers).status_code == 409

        day = client.get(f'/api/days/{today}').json()
        task_id = day['tasks'][0]['id']

        # Toggle done
        toggled = client.put(f'/api/days/{today}/tasks/{task_id}/done', headers=headers, json={'done': True})
        assert toggled.status_code == 200
        assert next(t for t in toggled.json()['tasks'] if t['id'] == task_id)['done'] is True

        # Set and clear time override
        overridden = client.put(
            f'/api/days/{today}/tasks/{task_id}/times',
            headers=headers,
            json={'start': '08:00', 'end': '08:30'},
        )
        assert overridden.status_code == 200
        assert next(t for t in overridden.json()['tasks'] if t['id'] == task_id)['override'] == {'start': '08:00', 'end': '08:30'}

        cleared = client.put(f'/api/days/{today}/tasks/{task_id}/times', headers=headers)
        assert cleared.status_code == 200
        assert next(t for t in cleared.json()['tasks'] if t['id'] == task_id)['override'] is None

        # Check-in & undo check-in
        checked = client.post(f'/api/days/{today}/check-in', headers=headers)
        assert checked.status_code == 200 and checked.json()['checked_at'] is not None
        unchecked = client.delete(f'/api/days/{today}/check-in', headers=headers)
        assert unchecked.status_code == 200 and unchecked.json()['checked_at'] is None
