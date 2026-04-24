class TestRegister:
    async def test_register_success(self, client):
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "strongpass123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data    

    async def test_register_duplicate_email(self, client, user):
        response = await client.post(
            "/auth/register",
            json={
                "email": "fixture@example.com", 
                "password": "strongpass123",
            },
        )
        assert response.status_code == 400
        error = response.json()["error"]
        assert error["code"] == "EMAIL_TAKEN"
        assert error["status"] == 400

    async def test_register_weak_password(self, client):
        response = await client.post(
            "/auth/register",
            json={
                "email": "bob@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"

    async def test_register_bad_email(self, client):
        response = await client.post(
            "/auth/register",
            json={
                "email": "notanemail",
                "password": "strongpass123",
            },
        )
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client, user):
        response = await client.post(
            "/auth/login",
            json={
                "email": "fixture@example.com",
                "password": "fixturepass123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, user):
        response = await client.post(
            "/auth/login",
            json={
                "email": "fixture@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "INVALID_CREDENTIALS"

    async def test_login_unknown_email(self, client):
        response = await client.post(
            "/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "strongpass123",
            },
        )
        assert response.status_code == 401


class TestGetMe:
    async def test_get_me_success(self, auth_client, user):
        response = await auth_client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["id"] == str(user.id)

    async def test_get_me_no_token(self, client):
        response = await client.get("/users/me")
        assert response.status_code in (401, 403)
    async def test_get_me_invalid_token(self, client):
        response = await client.get(
            "/users/me",
            headers={"Authorization": "Bearer faketoken123"},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "INVALID_TOKEN"