# moonBattery IoT Backend

A simple, production-ready REST API for managing moonBattery energy storage devices. Built with **Python 3.12**, **FastAPI**, and **PostgreSQL**.

> **Experience level:** Intermediate with Python, FastAPI, and SQLAlchemy. I chose technologies I am comfortable with and that are well-suited for this scope.

---

## Technology Choices & Justifications

| Technology | Why It Was Chosen |
|-----------|-------------------|
| **Python 3.12** | Allowed by the spec. Readable, widely used, excellent ecosystem. I have intermediate experience. |
| **FastAPI** | Best modern Python web framework. Automatic OpenAPI docs at `/docs`, built-in Pydantic validation, standard ASGI. Saves writing boilerplate validation and documentation code. |
| **SQLAlchemy 2.0** | The standard Python ORM. Clean declarative API, works with any SQL database, excellent documentation. More stable and standard than SQLModel (which is a wrapper around SQLAlchemy). |
| **PostgreSQL** | Production-grade open-source RDBMS. ACID compliance, handles concurrent writes safely (critical for IoT), better data integrity than SQLite. The spec says "database of your choice" — this is the safest production choice. |
| **Pydantic** | Required by FastAPI for request/response validation. Gives us automatic MAC address format checking and clear 422 errors without manual validation code. |
| **pytest + TestClient** | The spec requires tests. pytest is the Python standard. FastAPI's `TestClient` gives full HTTP round-trip testing without starting a server. |
| **Docker + Docker Compose** | The spec requires documenting setup. `docker compose up` gives reviewers a one-command way to run PostgreSQL + the API. This is the simplest possible onboarding. |
| **Synchronous code** | The spec has 3 simple CRUD endpoints with no concurrency requirements. Async (asyncpg, async SQLAlchemy, aiosqlite) adds significant complexity: greenlet dependencies, special test fixtures, harder debugging. Sync code is simpler, more readable, and easier to test. |
| **No Alembic** | For 2 tables in a coding challenge, Alembic is overkill. `SQLAlchemy.metadata.create_all()` on startup achieves the same result. In a real production system with many tables and a team, Alembic would be essential. |
| **No Poetry** | `requirements.txt` is the universal Python standard. Every developer understands it instantly. Poetry adds a learning curve and configuration burden not justified for this scope. |
| **`os.environ` instead of pydantic-settings** | Overkill for 2 environment variables. `os.environ.get()` has zero dependencies and is immediately obvious. |
| **Single `app/api.py`** | 3 endpoints do not need 3 router files + a service layer + a schemas file. Consolidating into one file reduces directory sprawl and makes the codebase navigable at a glance. |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose

### Run with Docker Compose
```bash
docker compose up --build
```
The API is available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### Run Tests
```bash
pip install -r requirements.txt
pytest -q
```

---

## API Endpoints

### Register a Device
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "aa:bb:cc:dd:ee:ff"}'
```
**Response `201 Created`:**
```json
{"serial_number": 1, "mac_address": "aa:bb:cc:dd:ee:ff", "created_at": "2024-01-15T09:30:00"}
```

### Ping a Device
```bash
curl -X POST http://localhost:8000/ping \
  -H "Content-Type: application/json" \
  -d '{"serial_number": 1}'
```
**Response `200 OK`:**
```json
{"serial_number": 1, "last_ping_at": "2024-01-15T10:00:00", "status": "ok"}
```

### Update Configuration
```bash
curl -X POST http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"serial_number": 1, "configs": {"power_mode": "eco", "max_charge": "80"}}'
```
**Response `200 OK`:**
```json
{"serial_number": 1, "updated_keys": ["power_mode", "max_charge"], "status": "ok"}
```

---

## Security Considerations (Bonus)

### Transport
- All endpoints must use **HTTPS** with TLS 1.2+.

### Authentication
- **`/register`** — Called on the production line by trusted equipment. Secure with an **API key** (`X-API-Key` header) or **mTLS** so only authorized manufacturing stations can create devices.
- **`/ping` and `/config`** — Called by deployed devices. Secure with a **Bearer token** (JWT or opaque token) issued at registration time, or **HMAC-signed requests** using a per-device shared secret injected during production.

### Rate Limiting
- Apply per-device rate limiting (e.g., 100 requests/minute) to prevent abuse.

---

## Project Structure

```
app/
  __init__.py
  settings.py       # 2 environment variables (DATABASE_URL, ENVIRONMENT)
  database.py       # Sync SQLAlchemy engine + session dependency
  models.py         # Device and Configuration tables
  api.py            # 3 endpoints + inline Pydantic schemas + inline business logic
  main.py           # FastAPI app factory with lifespan
tests/
  conftest.py       # Sync fixtures: in-memory SQLite, TestClient
  test_api.py       # 17 tests covering all endpoints
requirements.txt    # 6 dependencies
Dockerfile
docker-compose.yml
README.md
```

**Total source files:** ~10 (down from ~20).  
**Total dependencies:** 6 (down from 10+).
