# moonBattery IoT Backend

A small REST API for registering moonBattery devices, recording device pings, and storing device configuration key-value pairs. Built with **Python 3.12**, **FastAPI**, **SQLAlchemy 2.0**, and **PostgreSQL**.

> **Experience level:** Intermediate with Python, FastAPI, and SQLAlchemy. I chose technologies I am comfortable with and that are well-suited for this scope.

## Challenge Scope

The source challenge is [coding-challenge-backend.md](coding-challenge-backend.md). It asks for:

- A register endpoint that accepts a unique MAC address and returns a serial number.
- A ping endpoint that stores the device's last contact time.
- A configuration endpoint that accepts one or more key-value pairs.
- Production-minded organization, design, documentation, and tests.
- A README with setup instructions.
- Bonus documentation for securing device communication.

For requirement traceability, UML, code links, and test mapping, see [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md).

## Technology Choices

| Technology | Why it was chosen |
| --- | --- |
| Python 3.12 | Allowed by the spec, readable, widely used, and easy to maintain. |
| FastAPI | Gives request validation, response models, and OpenAPI docs at `/docs` with very little boilerplate. |
| SQLAlchemy 2.0 | Standard Python ORM with clear declarative models and PostgreSQL support. |
| PostgreSQL | Production-grade relational database with strong consistency for concurrent IoT writes. |
| Pydantic | Validates request payloads, including MAC address and configuration shape. |
| pytest + TestClient | Covers behavior through HTTP-level integration tests without starting a server. |
| Docker Compose | Gives developers a one-command API + database setup. |

The code is synchronous on purpose. The challenge has three simple write endpoints, and synchronous SQLAlchemy keeps the implementation easier to read, test, and explain. Database migrations are also intentionally omitted for this challenge-sized schema; `metadata.create_all()` creates the two tables on startup. In a long-lived production product, Alembic migrations would be the next step.

## Quick Start

### Prerequisites

- Docker and Docker Compose

### Run with Docker Compose

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`.

Interactive API docs are available at `http://localhost:8000/docs`.

### Run Tests Locally

```bash
pip install -r requirements.txt
pytest -q
```

## API Endpoints

### Register a Device

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "aa:bb:cc:dd:ee:ff"}'
```

Response `201 Created`:

```json
{
  "serial_number": 1,
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "created_at": "2024-01-15T09:30:00Z"
}
```

Registration is idempotent by MAC address. Re-registering the same MAC returns the same serial number.

### Ping a Device

```bash
curl -X POST http://localhost:8000/ping \
  -H "Content-Type: application/json" \
  -d '{"serial_number": 1}'
```

Response `200 OK`:

```json
{
  "serial_number": 1,
  "last_ping_at": "2024-01-15T10:00:00Z",
  "status": "ok"
}
```

### Update Configuration

```bash
curl -X POST http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"serial_number": 1, "configs": {"power_mode": "eco", "max_charge": "80"}}'
```

Response `200 OK`:

```json
{
  "serial_number": 1,
  "updated_keys": ["power_mode", "max_charge"],
  "status": "ok"
}
```

The endpoint accepts one or more configuration pairs. Existing keys are updated, new keys are inserted.

## Security Considerations

### Transport

All endpoints should run behind HTTPS with TLS 1.2+.

### Authentication

| Endpoint | Recommended protection |
| --- | --- |
| `/register` | API key or mTLS for trusted production-line equipment. |
| `/ping` | Per-device bearer token or HMAC-signed requests. |
| `/config` | Same per-device authentication as `/ping`, plus authorization checks if future admin writes are added. |

### Operational Controls

- Rate-limit by device serial number and source IP.
- Store secrets outside source control.
- Log rejected requests without leaking credentials.
- Add a `/health` endpoint before deploying behind a load balancer.

## Project Structure

```text
app/
  __init__.py
  settings.py       # Environment variables
  database.py       # SQLAlchemy engine and session dependency
  models.py         # Device and Configuration tables
  api.py            # Schemas, validation, and endpoint handlers
  main.py           # FastAPI app and startup table creation
tests/
  conftest.py       # Isolated SQLite test database fixtures
  test_api.py       # HTTP-level endpoint tests
requirements.txt
Dockerfile
docker-compose.yml
README.md
REQUIREMENTS_TRACEABILITY.md
```
