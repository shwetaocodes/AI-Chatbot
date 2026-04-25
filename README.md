# Chatbot API

AI Chatbot backend built with FastAPI, PostgreSQL, Redis, and Docker.

---

## Requirements

- Docker Desktop
- Docker Compose
- make

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourname/AiChatbot.git
cd AiChatbot
```

### 2. Create environment file

```bash
cp .env.example .env
```

Edit `.env` and fill in your values. Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start all services

```bash
make up
```

### 4. Run database migrations

```bash
make migrate
```

### 5. Verify everything is running

```bash
curl http://localhost:8000/health
# {"api":"ok","database":"ok","redis":"ok"}
```

Open Swagger UI: http://localhost:8000/docs

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `SYNC_DATABASE_URL` | ✅ | — | Sync PostgreSQL URL (`postgresql+psycopg2://...`) |
| `TEST_DATABASE_URL` | ✅ | — | Async PostgreSQL URL for test DB |
| `TEST_SYNC_DATABASE_URL` | ✅ | — | Sync PostgreSQL URL for test DB |
| `REDIS_URL` | ✅ | — | Redis connection URL |
| `SECRET_KEY` | ✅ | — | JWT signing key (min 32 chars) |
| `ALGORITHM` | ❌ | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `30` | Access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | ❌ | `7` | Refresh token TTL in days |

---

## Available Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | ❌ | API health check |
| `GET` | `/docs` | ❌ | Swagger UI |
| `POST` | `/auth/register` | ❌ | Register a new user |
| `POST` | `/auth/login` | ❌ | Login — returns access + refresh token |
| `POST` | `/auth/refresh` | ❌ | Exchange refresh token for new token pair |
| `POST` | `/auth/logout` | ❌ | Revoke refresh token |
| `GET` | `/users/me` | ✅ | Get current authenticated user |

### Error shape

All errors use a consistent JSON shape:

```json
{
  "error": {
    "code": "EMAIL_TAKEN",
    "message": "This email is already registered.",
    "status": 400
  }
}
```

### Auth flow

```
POST /auth/register → 201
POST /auth/login    → { access_token, refresh_token }
GET  /users/me      → Authorization: Bearer <access_token>
POST /auth/refresh  → { new_access_token, new_refresh_token }
POST /auth/logout   → 204
```

---

## Make Commands

| Command | Description |
|---|---|
| `make up` | Start all containers |
| `make down` | Stop all containers |
| `make build` | Rebuild after code changes |
| `make logs` | Follow API logs |
| `make migrate` | Apply database migrations |
| `make rollback` | Roll back last migration |
| `make migration msg="..."` | Generate new migration |
| `make test` | Run test suite |
| `make shell` | Bash into API container |
| `make db-shell` | psql into database container |

---

## Running Tests

```bash
make test

# With coverage report
docker exec -it chatbot_api pytest -v --cov=. --cov-report=term-missing
```

---

## CI/CD

GitHub Actions runs on every push and pull request to `main`:

1. **Lint** — ruff checks E, W, F, I rule sets
2. **Test** — pytest with PostgreSQL + Redis service containers, ≥ 80% coverage required
3. **Build** — Docker image build verified

---

## Project Structure

```
AiChatbot/
├── api/                  # HTTP routers (thin layer)
│   ├── auth.py           # POST /auth/*
│   ├── health.py         # GET /health
│   └── users.py          # GET /users/me
├── core/                 # Shared infrastructure
│   ├── config.py         # pydantic-settings
│   ├── database.py       # SQLAlchemy async engine
│   ├── dependencies.py   # get_current_user
│   ├── error_handlers.py # exception → JSON shape
│   ├── exceptions.py     # typed AppException subclasses
│   ├── middleware.py     # request logging
│   └── security.py       # JWT + bcrypt
├── models/               # SQLAlchemy ORM models
│   ├── base.py           # TimestampMixin
│   ├── conversation.py
│   ├── refresh_token.py
│   └── user.py
├── schemas/              # Pydantic request/response schemas
│   └── auth.py
├── services/             # Business logic
│   └── user_service.py
├── tests/
│   ├── conftest.py       # fixture stack
│   └── test_auth.py      # 31 auth tests
├── alembic/              # Database migrations
├── main.py               # FastAPI app + router registration
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── ruff.toml
└── .env.example
```