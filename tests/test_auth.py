from datetime import timedelta

import pytest
from freezegun import freeze_time

from core.security import create_access_token


class TestRegister:

    async def test_register_success(self, client):
        response = await client.post(
            "/auth/register",
            json={"email": "newuser@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data    # must never leak
        assert "password" not in data           # must never leak

    async def test_register_duplicate_email(self, client, user):
        response = await client.post(
            "/auth/register",
            json={"email": "fixture@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 400
        error = response.json()["error"]
        assert error["code"] == "EMAIL_TAKEN"
        assert error["status"] == 400
        assert "message" in error

    async def test_register_weak_password(self, client):
        response = await client.post(
            "/auth/register",
            json={"email": "bob@example.com", "password": "short"},
        )
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["status"] == 422

    async def test_register_bad_email(self, client):
        response = await client.post(
            "/auth/register",
            json={"email": "notanemail", "password": "strongpass123"},
        )
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"

    @pytest.mark.parametrize("payload,missing_field", [
        ({"password": "strongpass123"}, "email"),
        ({"email": "test@example.com"}, "password"),
        ({}, "email"),
    ])
    async def test_register_missing_fields(self, client, payload, missing_field):
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert missing_field in error["message"]

    @pytest.mark.parametrize("payload", [
        {"email": "bad", "password": "strongpass123"},          # bad email
        {"email": "test@example.com", "password": "tiny"},      # weak password
        {"email": "", "password": "strongpass123"},             # empty email
        {"email": "test@example.com", "password": ""},          # empty password
        {"email": "test@example.com", "password": "1234567"},   # 7 chars — just under limit
    ])
    async def test_register_invalid_payloads(self, client, payload):
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_password_exactly_8_chars(self, client):
        response = await client.post(
            "/auth/register",
            json={"email": "boundary@example.com", "password": "12345678"},
        )
        assert response.status_code == 201


class TestLogin:

    async def test_login_success(self, client, user):
        response = await client.post(
            "/auth/login",
            json={"email": "fixture@example.com", "password": "fixturepass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 10
        assert len(data["refresh_token"]) > 10

    async def test_login_wrong_password(self, client, user):
        response = await client.post(
            "/auth/login",
            json={"email": "fixture@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "INVALID_CREDENTIALS"

    async def test_login_unknown_email(self, client):
        response = await client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "INVALID_CREDENTIALS"

    async def test_login_error_messages_identical(self, client, user):
        r1 = await client.post(
            "/auth/login",
            json={"email": "fixture@example.com", "password": "wrong"},
        )
        r2 = await client.post(
            "/auth/login",
            json={"email": "nosuchuser@example.com", "password": "wrong"},
        )
        assert r1.json()["error"]["code"] == r2.json()["error"]["code"]
        assert r1.status_code == r2.status_code

    @pytest.mark.parametrize("payload", [
        {"password": "strongpass123"},
        {"email": "test@example.com"},
        {},
    ])
    async def test_login_missing_fields(self, client, payload):
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 422


class TestAccessToken:

    async def test_valid_token_accesses_protected_route(self, auth_client, user):
        response = await auth_client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["id"] == str(user.id)
        assert "hashed_password" not in data

    async def test_no_token_rejected(self, client):
        response = await client.get("/users/me")
        assert response.status_code in (401, 403)
    async def test_tampered_token_rejected(self, client):
        response = await client.get(
            "/users/me",
            headers={"Authorization": "Bearer eyJhbGci.tampered.signature"},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "INVALID_TOKEN"

    async def test_fake_token_rejected(self, client):
        response = await client.get(
            "/users/me",
            headers={"Authorization": "Bearer faketoken123"},
        )
        assert response.status_code == 401

    async def test_expired_token_rejected(self, client, user):
        with freeze_time("2026-01-01 12:00:00"):
            token = create_access_token(
                user_id=str(user.id),
                expires_delta=timedelta(minutes=1),
            )

        with freeze_time("2026-01-01 12:02:00"):
            response = await client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "INVALID_TOKEN"

    async def test_refresh_token_rejected_as_access_token(self, client, user):
        from datetime import datetime, timezone

        from jose import jwt

        from core.config import settings

        payload = {
            "sub": str(user.id),
            "type": "refresh",          # wrong type
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
        }
        fake_refresh = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {fake_refresh}"},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "INVALID_TOKEN"


class TestRefreshToken:

    async def _login(self, client, user):
        """Helper — logs in and returns both tokens."""
        response = await client.post(
            "/auth/login",
            json={"email": "fixture@example.com", "password": "fixturepass123"},
        )
        assert response.status_code == 200
        return response.json()

    async def test_refresh_returns_new_token_pair(self, client, user):
        tokens = await self._login(client, user)
        old_access = tokens["access_token"]
        old_refresh = tokens["refresh_token"]

        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != old_access
        assert data["refresh_token"] != old_refresh

    async def test_refreshed_access_token_works(self, client, user):
        tokens = await self._login(client, user)

        new_tokens = (await client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )).json()

        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert response.status_code == 200

    async def test_revoked_refresh_token_rejected(self, client, user):
        tokens = await self._login(client, user)
        refresh = tokens["refresh_token"]

        await client.post(
            "/auth/logout",
            json={"refresh_token": refresh},
        )

        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] in ("TOKEN_REVOKED", "INVALID_REFRESH_TOKEN")

    async def test_reuse_after_rotation_rejected(self, client, user):
        tokens = await self._login(client, user)
        old_refresh = tokens["refresh_token"]

        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert response.status_code == 200

        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert response.status_code == 401

    async def test_fake_refresh_token_rejected(self, client):
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": "completely-fake-token"},
        )
        assert response.status_code == 401

    async def test_expired_refresh_token_rejected(self, client, user):
        with freeze_time("2026-01-01 12:00:00"):
            tokens = await self._login(client, user)

        with freeze_time("2026-01-10 12:00:00"):
            response = await client.post(
                "/auth/refresh",
                json={"refresh_token": tokens["refresh_token"]},
            )

        assert response.status_code == 401

    async def test_refresh_missing_token_field(self, client):
        response = await client.post("/auth/refresh", json={})
        assert response.status_code == 422


class TestLogout:

    async def _login(self, client, user):
        response = await client.post(
            "/auth/login",
            json={"email": "fixture@example.com", "password": "fixturepass123"},
        )
        return response.json()

    async def test_logout_success(self, client, user):
        tokens = await self._login(client, user)
        response = await client.post(
            "/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 204

    async def test_logout_invalidates_refresh_token(self, client, user):
        tokens = await self._login(client, user)
        refresh = tokens["refresh_token"]

        await client.post("/auth/logout", json={"refresh_token": refresh})

        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert response.status_code == 401

    async def test_access_token_works_after_logout(self, client, user):
        tokens = await self._login(client, user)

        await client.post(
            "/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )

        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 200

    async def test_double_logout_rejected(self, client, user):
        tokens = await self._login(client, user)
        refresh = tokens["refresh_token"]

        await client.post("/auth/logout", json={"refresh_token": refresh})

        response = await client.post(
            "/auth/logout",
            json={"refresh_token": refresh},
        )
        assert response.status_code == 401

    async def test_logout_fake_token_rejected(self, client):
        response = await client.post(
            "/auth/logout",
            json={"refresh_token": "fake-token-xyz"},
        )
        assert response.status_code == 401

    async def test_logout_missing_token_field(self, client):
        response = await client.post("/auth/logout", json={})
        assert response.status_code == 422
