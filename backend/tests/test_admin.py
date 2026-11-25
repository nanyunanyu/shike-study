from fastapi.testclient import TestClient

from tests.conftest import bootstrap_users, login, make_client


def test_admin_dispatches_and_inbox(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as admin_client, TestClient(app) as user_client:
        admin_csrf = login(admin_client, 'admin')
        user_csrf = login(user_client, 'alice')
        admin_headers = {'X-CSRF-Token': admin_csrf}

        # Non-admin blocked from admin endpoints
        assert user_client.get('/api/admin/overview').status_code == 403

        overview = admin_client.get('/api/admin/overview').json()
        alice_id = next(u['id'] for u in overview['accounts'] if u['username'] == 'alice')

        payload = {
            'request_id': 'a' * 32,
            'recipient_ids': [alice_id],
            'kind': 'encouragement',
            'body': '继续保持专注！',
            'scheduled_for': None,
            'all_active': False,
        }
        send_res = admin_client.post('/api/admin/dispatches', headers=admin_headers, json=payload)
        assert send_res.status_code == 201, send_res.text
        dispatch_key = send_res.json()['key']

        # Same request_id + same body is idempotent; changed body -> 409
        replay = admin_client.post('/api/admin/dispatches', headers=admin_headers, json=payload)
        assert replay.status_code == 201 and replay.json()['key'] == dispatch_key
        tampered = admin_client.post('/api/admin/dispatches', headers=admin_headers, json=dict(payload, body='篡改内容'))
        assert tampered.status_code == 409

        # Sent dispatch detail & cannot cancel already sent dispatch
        detail = admin_client.get(f'/api/admin/dispatches/{dispatch_key}')
        assert detail.status_code == 200 and detail.json()['sent'] == 1
        assert admin_client.delete(f'/api/admin/dispatches/{dispatch_key}', headers=admin_headers).status_code == 409

        status = user_client.get('/api/messages/status').json()
        assert status['unread'] == 1
        assert status['pending'] is True

        inbox = user_client.get('/api/messages').json()
        assert len(inbox['items']) == 1
        msg_id = inbox['items'][0]['id']

        read_res = user_client.put(f'/api/messages/{msg_id}/read', headers={'X-CSRF-Token': user_csrf})
        assert read_res.status_code == 200
        assert read_res.json()['read_at'] is not None


def test_admin_user_lifecycle_and_inspection(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as admin_client, TestClient(app) as bob_client:
        admin_csrf = login(admin_client, 'admin')
        headers = {'X-CSRF-Token': admin_csrf}

        admin_id = next(u['id'] for u in admin_client.get('/api/admin/users').json() if u['role'] == 'admin')
        # Cannot deactivate or delete super admin
        assert admin_client.put(f'/api/admin/users/{admin_id}/active', headers=headers, json={'active': False}).status_code == 403
        assert admin_client.delete(f'/api/admin/users/{admin_id}', headers=headers).status_code == 403

        # Create student, duplicate fails 409
        created = admin_client.post(
            '/api/admin/users',
            headers=headers,
            json={'username': 'bob', 'password': 'Password123', 'must_change': False},
        )
        assert created.status_code == 201
        bob_id = created.json()['id']
        assert (
            admin_client.post(
                '/api/admin/users',
                headers=headers,
                json={'username': 'bob', 'password': 'Password123', 'must_change': False},
            ).status_code
            == 409
        )

        # Admin inspect endpoints (read-only day, plan, custom stats range)
        day_view = admin_client.get(f'/api/admin/users/{bob_id}/day/2026-11-25')
        assert day_view.status_code == 200 and day_view.json()['editable'] is False
        assert admin_client.get(f'/api/admin/users/{bob_id}/plan').status_code == 200
        stats_view = admin_client.get(f'/api/admin/users/{bob_id}/statistics?start=2026-11-20&end=2026-11-25')
        assert stats_view.status_code == 200 and len(stats_view.json()['custom_range']['days']) == 6

        # Deactivating bob immediately revokes bob's active session
        login(bob_client, 'bob')
        assert bob_client.get('/api/auth/me').status_code == 200
        assert admin_client.put(f'/api/admin/users/{bob_id}/active', headers=headers, json={'active': False}).status_code == 200
        assert bob_client.get('/api/auth/me').status_code == 401

        # Re-enable, reset password, and delete
        assert admin_client.put(f'/api/admin/users/{bob_id}/active', headers=headers, json={'active': True}).status_code == 200
        assert (
            admin_client.put(
                f'/api/admin/users/{bob_id}/password',
                headers=headers,
                json={'password': 'NewPassword456', 'must_change': False},
            ).status_code
            == 200
        )
        assert bob_client.post('/api/auth/login', json={'username': 'bob', 'password': 'NewPassword456'}).status_code == 200
        assert admin_client.delete(f'/api/admin/users/{bob_id}', headers=headers).status_code == 200
