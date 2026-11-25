from fastapi.testclient import TestClient

from tests.conftest import bootstrap_users, login, make_client


def test_plan_versions_optimistic_lock_and_categories_rules(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        csrf = login(client, 'alice')
        headers = {'X-CSRF-Token': csrf}

        plan = client.get('/api/plan').json()
        v1_id = plan['current']['id']
        assert client.get(f'/api/plan/versions/{v1_id}').status_code == 200
        assert client.get('/api/plan/versions/nonexistent').status_code == 404

        # Add a custom category
        categories = plan['categories'] + [{'id': 'math', 'name': '高数', 'archived': False, 'builtin': False}]
        saved_cats = client.put('/api/categories', headers=headers, json={'categories': categories})
        assert saved_cats.status_code == 200
        assert any(c['id'] == 'math' for c in saved_cats.json())

        # Cannot modify builtin category
        broken_builtin = [dict(c, name='篡改') if c['id'] == 'lecture' else c for c in categories]
        assert client.put('/api/categories', headers=headers, json={'categories': broken_builtin}).status_code == 422

        # Cannot delete existing category
        assert client.put('/api/categories', headers=headers, json={'categories': plan['categories']}).status_code == 422

        # Duplicate active category name rejected
        dup_cats = categories + [{'id': 'math2', 'name': '高数', 'archived': False, 'builtin': False}]
        assert client.put('/api/categories', headers=headers, json={'categories': dup_cats}).status_code == 422

        # Save new plan using custom category
        new_tasks = [{'id': 't1', 'title': '微积分', 'start': '09:00', 'end': '10:00', 'category': 'math', 'note': '', 'estimate': 60}]
        updated = client.put('/api/plan', headers=headers, json={'base': v1_id, 'tasks': new_tasks})
        assert updated.status_code == 200
        assert updated.json()['current']['id'] != v1_id

        # Stale base triggers optimistic lock 409
        stale = client.put('/api/plan', headers=headers, json={'base': v1_id, 'tasks': new_tasks})
        assert stale.status_code == 409

        # Cannot archive category still referenced in current plan
        archived_math = [dict(c, archived=True) if c['id'] == 'math' else c for c in categories]
        assert client.put('/api/categories', headers=headers, json={'categories': archived_math}).status_code == 409
