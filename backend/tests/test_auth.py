from fastapi.testclient import TestClient

from tests.conftest import bootstrap_users, login, make_client


def test_status_security_headers_and_csrf_protection(tmp_path):
    app, clock = make_client(tmp_path)
    with TestClient(app) as client:
        res = client.get('/api/status')
        assert res.status_code == 200
        assert res.json() == {'initialized': False}
        assert res.headers['X-Content-Type-Options'] == 'nosniff'
        assert res.headers['X-Frame-Options'] == 'DENY'
        assert res.headers['Referrer-Policy'] == 'no-referrer'
        assert res.headers['Cache-Control'] == 'no-store'

    bootstrap_users(app, clock)
    with TestClient(app) as client:
        assert client.get('/api/status').json() == {'initialized': True}

        # Cross-site / mismatched origin rejected by policy middleware
        cross = client.post(
            '/api/auth/login',
            headers={'Sec-Fetch-Site': 'cross-site'},
            json={'username': 'alice', 'password': 'Password123'},
        )
        assert cross.status_code == 403

        bad_origin = client.post(
            '/api/auth/login',
            headers={'Origin': 'https://evil.example'},
            json={'username': 'alice', 'password': 'Password123'},
        )
        assert bad_origin.status_code == 403

        csrf = login(client, 'alice')
        # Missing CSRF rejected on mutating API
        no_csrf = client.put('/api/preferences', json={'focus_minutes': 30})
        assert no_csrf.status_code == 403

        # Valid CSRF updates preferences
        ok = client.put(
            '/api/preferences',
            headers={'X-CSRF-Token': csrf},
            json={
                'focus_minutes': 35,
                'break_minutes': 10,
                'countdown_minutes': 45,
                'auto_break': True,
                'daily_focus_goal_minutes': 240,
                'appearance': 'dark',
                'palette': 'mint',
            },
        )
        assert ok.status_code == 200
        assert client.get('/api/auth/me').json()['preferences']['focus_minutes'] == 35

        # Logout revokes session
        out = client.post('/api/auth/logout', headers={'X-CSRF-Token': csrf})
        assert out.status_code == 200
        assert client.get('/api/auth/me').status_code == 401


def test_login_lockout_persists_across_requests(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock)
    with TestClient(app) as client:
        for attempt in range(4):
            res = client.post('/api/auth/login', json={'username': 'alice', 'password': f'wrong-{attempt}'})
            assert res.status_code == 401

        # 5th failure persists lockout and returns 429 + Retry-After
        locked = client.post('/api/auth/login', json={'username': 'alice', 'password': 'wrong-5'})
        assert locked.status_code == 429
        assert locked.headers['Retry-After'] == '900'

        # Even valid password is rejected while locked
        still_locked = client.post('/api/auth/login', json={'username': 'alice', 'password': 'Password123'})
        assert still_locked.status_code == 429
        assert int(still_locked.headers['Retry-After']) > 0

        # Lock expires after 900 seconds
        clock.advance(901)
        recovered = client.post('/api/auth/login', json={'username': 'alice', 'password': 'Password123'})
        assert recovered.status_code == 200


def test_must_change_password_and_session_invalidation(tmp_path):
    app, clock = make_client(tmp_path)
    bootstrap_users(app, clock, alice_must_change=True)
    with TestClient(app) as client1, TestClient(app) as client2:
        csrf1 = login(client1, 'alice')
        login(client2, 'alice')

        # Normal endpoint blocked until initial password is changed
        assert client1.get('/api/days/2026-11-25').status_code == 403
        assert client1.get('/api/auth/me').status_code == 200

        # Wrong current password -> 400; same password -> 422
        assert (
            client1.post(
                '/api/auth/password',
                headers={'X-CSRF-Token': csrf1},
                json={'current': 'badpass', 'password': 'NewPassword123'},
            ).status_code
            == 400
        )
        assert (
            client1.post(
                '/api/auth/password',
                headers={'X-CSRF-Token': csrf1},
                json={'current': 'Password123', 'password': 'Password123'},
            ).status_code
            == 422
        )

        # Valid password change lifts gate and revokes other sessions
        changed = client1.post(
            '/api/auth/password',
            headers={'X-CSRF-Token': csrf1},
            json={'current': 'Password123', 'password': 'NewPassword123'},
        )
        assert changed.status_code == 200
        assert changed.json()['user']['must_change'] is False
        assert client1.get('/api/days/2026-11-25').status_code == 200
        assert client2.get('/api/auth/me').status_code == 401
