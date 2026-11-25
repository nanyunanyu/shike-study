from fastapi.testclient import TestClient

from tests.conftest import bootstrap_users, login, make_client


def test_messages_preview_read_delete_and_schedule(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as admin_client, TestClient(app) as user_client:
        admin_csrf = login(admin_client, 'admin')
        user_csrf = login(user_client, 'alice')
        admin_headers = {'X-CSRF-Token': admin_csrf}
        user_headers = {'X-CSRF-Token': user_csrf}

        alice_id = next(u['id'] for u in admin_client.get('/api/admin/users').json() if u['username'] == 'alice')

        # Immediate message + scheduled future message
        m1 = admin_client.post(
            f'/api/admin/users/{alice_id}/messages',
            headers=admin_headers,
            json={'kind': 'encouragement', 'body': '立即送达的消息', 'scheduled_for': None},
        )
        assert m1.status_code == 201
        m2 = admin_client.post(
            f'/api/admin/users/{alice_id}/messages',
            headers=admin_headers,
            json={'kind': 'reminder', 'body': '定时一小时后送达', 'scheduled_for': '2026-11-25T11:00'},
        )
        assert m2.status_code == 201

        # Before 11:00 only m1 is visible in inbox; m2 is in admin pending list
        assert user_client.get('/api/messages/status').json() == {'unread': 1, 'pending': True}
        assert len(admin_client.get(f'/api/admin/users/{alice_id}/messages').json()) == 1

        preview = user_client.post('/api/messages/preview', headers=user_headers)
        assert preview.status_code == 200
        assert preview.json()['message']['body'] == '立即送达的消息'
        assert preview.json()['more'] == 0
        assert user_client.post('/api/messages/preview', headers=user_headers).json() is None

        msg_id = m1.json()['id']
        assert user_client.put(f'/api/messages/{msg_id}/read', headers=user_headers).json()['read_at'] is not None
        assert user_client.delete(f'/api/messages/{msg_id}', headers=user_headers).status_code == 200
        assert user_client.get('/api/messages').json()['items'] == []

        # Advance past 11:00 -> scheduled message arrives and can no longer be canceled
        clock.advance(3600)
        assert user_client.get('/api/messages/status').json()['unread'] == 1
        assert admin_client.delete(f"/api/admin/users/{alice_id}/messages/{m2.json()['id']}", headers=admin_headers).status_code == 409
