# 01 — Requirements Analysis

## Project: moonBattery IoT Backend

### Overview

The moonBattery is a distributed energy storage system that stores power produced by lunar-cells. Each physical battery unit must register with a central cloud backend during production, periodically report its health via ping, and synchronize its internal configuration database with the backend.

This document captures the full set of functional, non-functional, and security requirements.

---

## Functional Requirements

### FR-1: Device Registration (`POST /register`)

| Field | Detail |
|-------|--------|
| **Purpose** | Register a moonBattery during the production line so it becomes known to the backend. |
| **Input** | Unique MAC address of the device (e.g., `aa:bb:cc:dd:ee:ff`). |
| **Output** | A unique serial number (e.g., `123456`) assigned by the backend. |
| **Validation** | MAC address must conform to standard IEEE 802 MAC-48 / EUI-48 format (`XX:XX:XX:XX:XX:XX` or `XX-XX-XX-XX-XX-XX`). |
| **Error Conditions** | Duplicate MAC address → `409 Conflict`. Malformed MAC → `422 Unprocessable Entity`. |
| **Idempotency** | Re-submitting the same MAC should return the same serial number (UPSERT semantics). |

### FR-2: Heartbeat Ping (`POST /ping`)

| Field | Detail |
|-------|--------|
| **Purpose** | Allow the backend to track device liveness and know when a battery was last online. |
| **Input** | Serial number previously issued during registration. |
| **Output** | Acknowledgment including the updated `last_ping_at` timestamp. |
| **Error Conditions** | Unknown serial number → `404 Not Found`. Malformed serial → `422 Unprocessable Entity`. |
| **Side Effects** | Update `last_ping_at` on the `devices` record to the current server time. |

### FR-3: Configuration Synchronization (`POST /config`)

| Field | Detail |
|-------|--------|
| **Purpose** | Synchronize one or more key-value configuration pairs from the device to the backend. |
| **Input** | Serial number + a dictionary of key-value pairs (`{"key1": "val1", "key2": "val2"}`). |
| **Output** | Acknowledgment with a list of keys that were updated. |
| **Error Conditions** | Unknown serial number → `404 Not Found`. Empty config payload → `422 Unprocessable Entity`. |
| **Side Effects** | Insert new keys or update existing values for the device. Store `updated_at` per key. |
| **Batch Semantics** | All keys in a single request must be applied atomically (all succeed or none). |

---

## Non-Functional Requirements

### NFR-1: Performance
- API response latency < 200 ms p95 for all endpoints under normal load.
- Support at least 1,000 concurrent devices pinging every 30 seconds.

### NFR-2: Reliability
- Persist all state to PostgreSQL; in-memory-only storage is not acceptable.
- Handle duplicate registration attempts gracefully (idempotent).

### NFR-3: Maintainability
- Follow a layered architecture (API → Service → Data Access) so business logic is decoupled from HTTP and DB concerns.
- Use type hints, Pydantic models, and automated linting (ruff / mypy).
- Document all public interfaces with docstrings.

### NFR-4: Observability
- Include structured logging for every request.
- Return consistent error schemas (`detail`, `type`, `status_code`) so clients can programmatically handle failures.

### NFR-5: Testability
- Achieve > 80 % line coverage with automated tests.
- Unit tests for pure business logic.
- Integration tests that exercise full HTTP → DB round-trips.

---

## Security Requirements (Bonus — Documented)

### SR-1: Transport Security
- All communication between moonBattery and backend must occur over **TLS 1.2+** (HTTPS).

### SR-2: Registration Endpoint Security
- The `/register` endpoint is called on the **production line** by trusted manufacturing equipment.
- Recommended: **API Key** or **mTLS** so only authorized production stations can create new devices.

### SR-3: Device Endpoint Security
- `/ping` and `/config` are called by deployed devices in the field.
- Recommended: **Bearer Token (JWT or opaque token)** issued at registration time.
- Token should be short-lived (e.g., 24 h) with refresh support, or use HMAC-signed requests with a device-shared secret.

### SR-4: Input Validation
- Reject oversized payloads (> 1 MB for config).
- Strict MAC format validation to prevent injection or scanning attacks.
- Rate-limit endpoints (e.g., 10 req/s per IP / per device) to mitigate abuse.

---

## User Stories

1. **As a production engineer**, I want to register a new moonBattery by its MAC address so that the backend can assign it a serial number.
2. **As a field technician**, I want the device to ping the backend periodically so that I can monitor device uptime and detect outages.
3. **As a system administrator**, I want device configurations synced to the backend so that I can audit and manage settings remotely.

---

## Out of Scope (for this iteration)

- Device firmware over-the-air (OTA) updates.
- Real-time dashboards or alerting.
- Multi-tenant / multi-region deployments.
- Actual implementation of authentication middleware (documented only, per project decision).
