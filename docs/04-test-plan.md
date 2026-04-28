# 04 — Test Plan

## Testing Strategy

We employ a **pyramid** approach:
- **Unit tests** for pure logic (MAC normalization, serial generation logic).
- **Integration tests** for HTTP → Service → Database round-trips (primary focus).
- **End-to-end smoke tests** via curl / manual verification.

Test runner: **pytest** with `pytest-asyncio` and `httpx.AsyncClient` against a FastAPI `TestClient` equivalent.

Database for tests: A **dedicated PostgreSQL database** (e.g., `moonbattery_test`) or SQLite async fallback to ensure isolation. Each test runs inside a transaction that is rolled back on teardown.

---

## Test Coverage Targets

| Layer | Target |
|-------|--------|
| `app/services.py` | 100 % |
| `app/routers/*.py` | 100 % |
| `app/schemas.py` | 100 % (via Pydantic validation tests) |
| `app/models.py` | > 80 % |
| **Overall** | **> 90 %** |

---

## Test Cases

### Module: `tests/test_register.py`

| # | Test Name | Scenario | Expected Result |
|---|-----------|----------|-----------------|
| R1 | `test_register_new_device` | Valid MAC `aa:bb:cc:dd:ee:ff` | `201 Created`, serial number assigned, created_at set |
| R2 | `test_register_idempotent` | Submit same MAC twice | Second call returns `200 OK` with same serial number |
| R3 | `test_register_invalid_mac_format` | MAC = `not-a-mac` | `422 Unprocessable Entity` with clear validation error |
| R4 | `test_register_mac_normalization` | MAC = `AA:BB:CC:DD:EE:FF` | Stored as lowercase `aa:bb:cc:dd:ee:ff` |
| R5 | `test_register_mac_dash_format` | MAC = `aa-bb-cc-dd-ee-ff` | Accepted and normalized to colon format |
| R6 | `test_register_empty_body` | Request body = `{}` | `422 Unprocessable Entity` |

---

### Module: `tests/test_ping.py`

| # | Test Name | Scenario | Expected Result |
|---|-----------|----------|-----------------|
| P1 | `test_ping_existing_device` | Serial = registered device | `200 OK`, `last_ping_at` updated to near-now |
| P2 | `test_ping_updates_timestamp` | Call ping twice, compare timestamps | Second timestamp > first timestamp |
| P3 | `test_ping_unknown_device` | Serial = 999999 (non-existent) | `404 Not Found` |
| P4 | `test_ping_invalid_serial` | Serial = `"abc"` (string) | `422 Unprocessable Entity` |
| P5 | `test_ping_missing_serial` | Body = `{}` | `422 Unprocessable Entity` |

---

### Module: `tests/test_config.py`

| # | Test Name | Scenario | Expected Result |
|---|-----------|----------|-----------------|
| C1 | `test_config_create_new_keys` | New device, configs `{"a": "1", "b": "2"}` | `200 OK`, `updated_keys` = `["a", "b"]` |
| C2 | `test_config_update_existing_keys` | Existing key `a=1`, send `a=2` | Value updated to `2`, `updated_at` changed |
| C3 | `test_config_mixed_insert_update` | One new key, one existing key | Both handled correctly, all keys in response |
| C4 | `test_config_unknown_device` | Serial = 999999 | `404 Not Found` |
| C5 | `test_config_empty_configs` | Body = `{"serial_number": 1, "configs": {}}` | `422 Unprocessable Entity` |
| C6 | `test_config_missing_configs` | Body = `{"serial_number": 1}` | `422 Unprocessable Entity` |
| C7 | `test_config_persists_values` | Store config, fetch device (via DB) | Values retrievable in DB |

---

## Edge Cases & Stress Tests

| # | Scenario | Approach |
|---|----------|----------|
| E1 | **Concurrent registration** of same MAC | Two parallel requests → only one insert succeeds, both return same serial (handled by DB unique constraint + UPSERT logic) |
| E2 | **Very long config values** | Value length = 10,000 chars → accepted and stored correctly |
| E3 | **Many config keys** | 100 keys in one request → all applied atomically |
| E4 | **Special characters in config values** | Unicode, newlines, JSON-like strings → stored verbatim |
| E5 | **Case sensitivity of MAC** | `AA:BB:CC:DD:EE:FF` vs `aa:bb:cc:dd:ee:ff` → treated as same device |

---

## Running Tests

### Inside Docker (Recommended)
```bash
docker compose run --rm app pytest -q --tb=short
```

### With Coverage Report
```bash
docker compose run --rm app pytest --cov=app --cov-report=term-missing
```

### Watch Mode (Local Development)
```bash
pytest -f  # or pytest-watch
```

---

## CI/CD Integration (Recommended Future Step)

A GitHub Actions workflow should:
1. Spin up PostgreSQL service container.
2. Install Python dependencies.
3. Run `alembic upgrade head`.
4. Run `pytest --cov=app --cov-fail-under=90`.
5. Run `ruff check .` and `mypy app/`.
6. Build Docker image.
