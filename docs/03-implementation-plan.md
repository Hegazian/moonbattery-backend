# 03 — Implementation Plan

## Phase Overview

This document breaks the build into 6 concrete phases, each with deliverables and verification steps.

---

## Phase 1: Project Bootstrap

**Goal:** Establish a reproducible development environment and project skeleton.

**Tasks:**
1. Create `pyproject.toml` with dependencies:
   - `fastapi`, `uvicorn[standard]`, `sqlmodel`, `asyncpg`, `alembic`, `pydantic-settings`
   - Dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`
2. Create `Dockerfile` (multi-stage or slim Python image).
3. Create `docker-compose.yml` with:
   - `app` service (FastAPI + Uvicorn)
   - `db` service (PostgreSQL 15 with healthcheck)
4. Create directory structure:
   ```
   app/
   ├── __init__.py
   ├── main.py              # FastAPI app factory + lifespan
   ├── config.py            # Pydantic-settings (env vars)
   ├── database.py          # SQLModel engine + session dependency
   ├── models.py            # SQLModel table definitions
   ├── schemas.py           # Pydantic request/response models
   ├── services.py          # Business logic (register, ping, config)
   ├── dependencies.py      # DB session injector
   └── routers/
       ├── __init__.py
       ├── register.py
       ├── ping.py
       └── config.py
   tests/
   ├── conftest.py          # pytest fixtures (async client, test DB)
   ├── test_register.py
   ├── test_ping.py
   └── test_config.py
   alembic/
   ├── env.py
   ├── script.py.mako
   └── versions/
   docs/
   ├── 01-requirements.md
   ├── 02-design.md
   ├── 03-implementation-plan.md
   └── 04-test-plan.md
   ```
5. Add `.gitignore` (Python defaults).

**Verification:**
- `docker compose build` completes without errors.
- `docker compose up db` starts PostgreSQL successfully.

---

## Phase 2: Database Layer

**Goal:** Define persistent models and schema migrations.

**Tasks:**
1. Implement `models.py`:
   - `Device` table (id, mac_address, serial_number, last_ping_at, created_at)
   - `Configuration` table (id, device_id, key, value, updated_at)
   - Relationship: `Device.configurations` (lazy select)
2. Configure Alembic (`alembic init` + customize `env.py` for async SQLAlchemy).
3. Generate initial migration:
   ```bash
   alembic revision --autogenerate -m "init"
   alembic upgrade head
   ```
4. Implement `database.py`:
   - `create_engine()` with async `postgresql+asyncpg` URL.
   - `get_session()` dependency yielding `AsyncSession`.

**Verification:**
- Migration applies cleanly inside Docker.
- Tables exist in PostgreSQL (`\dt` in psql).

---

## Phase 3: Business Logic (Services)

**Goal:** Encapsulate domain logic, decoupled from HTTP concerns.

**Tasks:**
1. **`register_device(mac_address: str, session)` → `Device`**
   - Normalize MAC to lowercase with colons.
   - Query existing device by MAC.
   - If found, return existing (idempotent).
   - If not found, `INSERT` with auto-increment `serial_number`.
   - Handle `IntegrityError` → raise custom `DuplicateDeviceError`.

2. **`ping_device(serial_number: int, session)` → `Device`**
   - Query device by `serial_number`.
   - If not found, raise `DeviceNotFoundError`.
   - Update `last_ping_at = func.now()`.
   - Return updated device.

3. **`update_config(serial_number: int, configs: dict, session)` → list[str]`**
   - Query device by `serial_number`.
   - If not found, raise `DeviceNotFoundError`.
   - For each `(key, value)` pair:
     - `INSERT INTO configurations … ON CONFLICT (device_id, key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()`
   - Return list of updated keys.

**Verification:**
- Unit tests for each service pass (Phase 6).

---

## Phase 4: API Layer (Routers + Schemas)

**Goal:** Expose services via RESTful HTTP endpoints.

**Tasks:**
1. **`schemas.py`**
   - `RegisterRequest(mac_address: str)`
   - `RegisterResponse(serial_number: int, mac_address: str, created_at: datetime)`
   - `PingRequest(serial_number: int)`
   - `PingResponse(serial_number: int, last_ping_at: datetime, status: str)`
   - `ConfigRequest(serial_number: int, configs: dict[str, str])`
   - `ConfigResponse(serial_number: int, updated_keys: list[str], status: str)`

2. **`routers/register.py`**
   - `POST /register`
   - Parse request → call `services.register_device()` → return 201 / 200.

3. **`routers/ping.py`**
   - `POST /ping`
   - Parse request → call `services.ping_device()` → return 200.

4. **`routers/config.py`**
   - `POST /config`
   - Parse request → call `services.update_config()` → return 200.

5. **`main.py`**
   - Create `FastAPI` app with lifespan context (create tables on startup for dev/tests).
   - Include routers with tags.
   - Register global exception handlers for `DuplicateDeviceError`, `DeviceNotFoundError`.

**Verification:**
- Start server locally (`uvicorn app.main:app --reload`).
- Swagger UI (`/docs`) shows all 3 endpoints correctly.
- Manual curl smoke tests pass.

---

## Phase 5: Testing Infrastructure

**Goal:** Ensure correctness via automated tests.

**Tasks:**
1. **`tests/conftest.py`**
   - Fixture: `async_client` — `httpx.AsyncClient` pointing to FastAPI test app.
   - Fixture: `db_session` — isolated `AsyncSession` using test database or in-memory SQLite fallback (if PostgreSQL unavailable).
   - Fixture: `init_db` — create/drop tables before/after test suite.

2. **Write test modules** (see `docs/04-test-plan.md` for full case list).

**Verification:**
- `pytest -q` passes with 100 % success rate.

---

## Phase 6: Documentation & Polish

**Goal:** Make the project production-presentable.

**Tasks:**
1. **`README.md`**
   - Project description
   - Prerequisites (Docker, Docker Compose)
   - Quick start commands (`docker compose up`)
   - API usage examples (curl)
   - Running tests (`docker compose run --rm app pytest`)
   - Security documentation (bonus)
2. Run `ruff check .` and `ruff format .` — zero warnings.
3. Run `mypy app/` — zero errors.
4. Verify all docs are up-to-date.

**Verification:**
- README instructions work on a clean machine (simulated by reviewer).
- Lint/type checks pass.
- All tests green.

---

## Estimated Effort

| Phase | Estimated Time |
|-------|----------------|
| 1. Bootstrap | 30 min |
| 2. Database | 30 min |
| 3. Services | 45 min |
| 4. API Layer | 45 min |
| 5. Testing | 60 min |
| 6. Docs & Polish | 30 min |
| **Total** | **~4 hours** |
