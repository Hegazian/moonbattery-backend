# 02 — System Design

## Architecture Overview

```
┌──────────────┐      HTTPS      ┌──────────────────┐      SQL/TCP      ┌─────────────┐
│  moonBattery │ ───────────────> │  FastAPI (Uvicorn)│ ───────────────> │  PostgreSQL  │
│   (Device)   │                  │  Python 3.12      │                  │   15+        │
└──────────────┘                  └──────────────────┘                  └─────────────┘
                                         │
                                         v
                                   ┌─────────────┐
                                   │  Alembic    │
                                   │  Migrations │
                                   └─────────────┘
```

---

## Technology Choices

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Language** | Python 3.12 | Readable, vast ecosystem, excellent async support. |
| **Framework** | FastAPI | Automatic OpenAPI docs, Pydantic integration, async I/O, type-safe. |
| **Database** | PostgreSQL 15 | ACID compliance, robust JSON support, production-proven. |
| **ORM / Models** | SQLModel 0.0.x | Bridges SQLAlchemy 2.0 and Pydantic v2; single source of truth for schemas. |
| **Migrations** | Alembic | Industry standard for SQLAlchemy schema versioning. |
| **Testing** | pytest + httpx | Native async test support, ASGI test client via `httpx.AsyncClient`. |
| **Lint / Type** | ruff + mypy | Fast linting + static type checking. |
| **Container** | Docker + Compose | One-command local setup, reproducible environment. |

---

## Database Schema

### Table: `devices`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Internal surrogate key. |
| `mac_address` | `VARCHAR(17)` | `UNIQUE NOT NULL` | Normalized lowercase with colons (`aa:bb:cc:dd:ee:ff`). |
| `serial_number` | `INTEGER` | `UNIQUE NOT NULL` | Auto-incrementing integer (e.g., `1`, `2`, `123456`). |
| `last_ping_at` | `TIMESTAMP WITH TIME ZONE` | `NULL` | Last time the device called `/ping`. |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | `DEFAULT now()` | Registration timestamp. |

**Indexes:**
- `idx_devices_mac_address` (unique, for fast lookup during registration).
- `idx_devices_serial_number` (unique, for fast lookup during ping/config).

### Table: `configurations`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Internal surrogate key. |
| `device_id` | `INTEGER` | `FOREIGN KEY (devices.id) ON DELETE CASCADE` | Parent device. |
| `key` | `VARCHAR(255)` | `NOT NULL` | Configuration key name. |
| `value` | `TEXT` | `NOT NULL` | Configuration value. |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | `DEFAULT now()` | Last update timestamp. |

**Constraints:**
- `UNIQUE(device_id, key)` — one row per device-key pair.

**Indexes:**
- `idx_configurations_device_id_key` (unique composite, for upsert lookup).

---

## API Specification

### OpenAPI Base
- **Base URL:** `http://localhost:8000`
- **Content-Type:** `application/json`
- **Docs:** Auto-generated at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### Endpoints

#### `POST /register`

**Request Body:**
```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff"
}
```

**Response `201 Created`:**
```json
{
  "serial_number": 123456,
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "created_at": "2024-01-15T09:30:00Z"
}
```

**Error `409 Conflict`:**
```json
{
  "detail": "Device with MAC address aa:bb:cc:dd:ee:ff is already registered."
}
```

**Error `422 Unprocessable Entity`:**
```json
{
  "detail": [
    {
      "loc": ["body", "mac_address"],
      "msg": "value is not a valid MAC address",
      "type": "value_error.macaddress"
    }
  ]
}
```

---

#### `POST /ping`

**Request Body:**
```json
{
  "serial_number": 123456
}
```

**Response `200 OK`:**
```json
{
  "serial_number": 123456,
  "last_ping_at": "2024-01-15T10:00:00Z",
  "status": "ok"
}
```

**Error `404 Not Found`:**
```json
{
  "detail": "Device with serial number 123456 not found."
}
```

---

#### `POST /config`

**Request Body:**
```json
{
  "serial_number": 123456,
  "configs": {
    "power_mode": "eco",
    "max_charge_rate": "80"
  }
}
```

**Response `200 OK`:**
```json
{
  "serial_number": 123456,
  "updated_keys": ["power_mode", "max_charge_rate"],
  "status": "ok"
}
```

**Error `404 Not Found`:**
```json
{
  "detail": "Device with serial number 123456 not found."
}
```

**Error `422 Unprocessable Entity`:**
```json
{
  "detail": [
    {
      "loc": ["body", "configs"],
      "msg": "configs must contain at least one key-value pair",
      "type": "value_error"
    }
  ]
}
```

---

## Data Flow Diagrams

### Registration Flow

```
Device (MAC) → POST /register
                    │
                    ▼
            Validate MAC format (Pydantic)
                    │
                    ▼
            Check DB for existing MAC
              ├─ Found → Return existing serial (200)
              └─ Not found → Insert device, return new serial (201)
```

### Ping Flow

```
Device (Serial) → POST /ping
                      │
                      ▼
              Validate serial (Pydantic)
                      │
                      ▼
              Lookup device by serial
                ├─ Not found → 404
                └─ Found → Update last_ping_at, return timestamp (200)
```

### Configuration Flow

```
Device (Serial + KV pairs) → POST /config
                                 │
                                 ▼
                         Validate payload (Pydantic)
                                 │
                                 ▼
                         Lookup device by serial
                           ├─ Not found → 404
                           └─ Found → BEGIN TX
                                       ├─ For each (key, value):
                                       │   UPSERT into configurations
                                       │   (INSERT … ON CONFLICT DO UPDATE)
                                       └─ COMMIT
                                       Return updated keys (200)
```

---

## Error Handling Strategy

| Exception Type | HTTP Status | Log Level | Example |
|----------------|-------------|-----------|---------|
| `ValidationError` (Pydantic) | `422` | WARNING | Malformed MAC address |
| `IntegrityError` (Duplicate MAC) | `409` | WARNING | Re-register existing device |
| `DeviceNotFoundError` (Custom) | `404` | INFO | Unknown serial on ping/config |
| `Unhandled Exception` | `500` | ERROR | Unexpected server error |

All errors return a consistent JSON body:
```json
{
  "detail": "Human-readable message"
}
```

---

## Scaling Considerations (Future)

- **Read Replicas:** If ping volume grows, off-load read queries to replicas.
- **Connection Pooling:** Use `asyncpg` pool (default in SQLAlchemy async) with size tuned to expected concurrency.
- **Batching:** Config endpoint already accepts multiple keys; consider batch ping endpoints for fleet-wide updates.
- **Caching:** Cache device lookups in Redis if ping rate > 10k RPS.
