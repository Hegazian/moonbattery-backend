# moonBattery IoT Backend

A production-ready REST API for managing moonBattery energy storage devices. Built with **Python 3.12**, **FastAPI**, and **PostgreSQL**.

---

## Features

- **Device Registration** — Register a new moonBattery via its unique MAC address and receive a serial number.
- **Heartbeat Ping** — Devices periodically ping the backend to report liveness.
- **Configuration Sync** — Synchronize key-value configuration pairs from device to backend.
- **Auto-generated API Docs** — Interactive Swagger UI at `/docs` and ReDoc at `/redoc`.
- **Database Migrations** — Managed via Alembic.
- **Comprehensive Tests** — pytest suite with > 90 % coverage.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12 |
| Framework | FastAPI |
| Database | PostgreSQL 15 (production) / SQLite (tests) |
| ORM | SQLModel (SQLAlchemy 2.0 + Pydantic) |
| Migrations | Alembic |
| Testing | pytest, pytest-asyncio, httpx |
| Lint / Format | ruff, mypy |
| Container | Docker + Docker Compose |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- Or local Python 3.12+ with `pip`

### Option 1: Docker Compose (Recommended)

```bash
# Clone / navigate to project directory
cd moonbattery-backend

# Start PostgreSQL + API server
docker compose up --build

# API will be available at http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

Run database migrations manually (if needed):
```bash
docker compose run --rm app alembic upgrade head
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt  # or poetry install

# Set environment variables (or create .env)
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/moonbattery"

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Usage

### Register a Device

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "aa:bb:cc:dd:ee:ff"}'
```

**Response `201 Created`:**
```json
{
  "serial_number": 1,
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "created_at": "2024-01-15T09:30:00+00:00"
}
```

### Ping a Device

```bash
curl -X POST http://localhost:8000/ping \
  -H "Content-Type: application/json" \
  -d '{"serial_number": 1}'
```

**Response `200 OK`:**
```json
{
  "serial_number": 1,
  "last_ping_at": "2024-01-15T10:00:00+00:00",
  "status": "ok"
}
```

### Update Configuration

```bash
curl -X POST http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": 1,
    "configs": {
      "power_mode": "eco",
      "max_charge_rate": "80"
    }
  }'
```

**Response `200 OK`:**
```json
{
  "serial_number": 1,
  "updated_keys": ["power_mode", "max_charge_rate"],
  "status": "ok"
}
```

---

## Running Tests

### Inside Docker
```bash
docker compose run --rm app pytest -q
```

### Locally
```bash
pytest -q
```

### With Coverage
```bash
pytest --cov=app --cov-report=term-missing
```

---

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Environment settings
│   ├── database.py          # DB engine & session
│   ├── models.py            # SQLModel tables
│   ├── schemas.py           # Pydantic request/response models
│   ├── services.py          # Business logic
│   ├── dependencies.py      # FastAPI DI
│   └── routers/
│       ├── __init__.py
│       ├── register.py
│       ├── ping.py
│       └── config.py
├── tests/
│   ├── conftest.py          # pytest fixtures
│   ├── test_register.py
│   ├── test_ping.py
│   └── test_config.py
├── alembic/                 # Database migrations
├── docs/                    # Project documentation
│   ├── 01-requirements.md
│   ├── 02-design.md
│   ├── 03-implementation-plan.md
│   └── 04-test-plan.md
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## Security Considerations (Bonus)

This section documents how communication between moonBattery devices and the backend should be secured in a production deployment.

### Transport Layer Security (TLS)

- **All endpoints must use HTTPS** with TLS 1.2 or higher.
- Devices should validate the server certificate (pinning recommended for IoT).

### Authentication by Endpoint

#### `/register` — Production-Line Authentication
- Called by **trusted manufacturing equipment** during device production.
- **Recommended:** API Key passed in a custom header (`X-API-Key`).
- **Alternative:** Mutual TLS (mTLS) where both client and server present certificates.
- API keys should be rotated regularly and stored in a secrets manager (e.g., HashiCorp Vault, AWS Secrets Manager).

#### `/ping` and `/config` — Device Authentication
- Called by **deployed moonBattery devices** in the field.
- **Recommended:** Bearer Token (JWT or opaque token) issued at registration time.
  - Token includes claims: `serial_number`, `iat`, `exp`.
  - Short expiration (e.g., 24 hours) with a refresh endpoint.
- **Alternative:** HMAC-signed requests using a per-device shared secret injected during production.
  - Device signs the request payload + timestamp.
  - Backend verifies the signature against the stored secret.

### Rate Limiting

- Implement per-IP and per-device rate limiting (e.g., 10 requests/second) to prevent abuse.
- Use a Redis-backed rate limiter for distributed deployments.

### Input Validation

- All endpoints enforce strict Pydantic validation.
- MAC addresses are normalized and validated against IEEE 802 format.
- Config payload size is implicitly bounded by JSON parser limits; explicit max size middleware is recommended.

---

## License

This project is provided as a coding challenge submission.
