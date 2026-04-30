"""Tests for all three API endpoints."""

from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Configuration, Device


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


def test_register_new_device(client: TestClient, db: Session) -> None:
    response = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    assert response.status_code == 201
    data = response.json()
    assert data["serial_number"] == 1
    assert data["mac_address"] == "aa:bb:cc:dd:ee:ff"

    device = db.scalar(select(Device).where(Device.mac_address == "aa:bb:cc:dd:ee:ff"))
    assert device is not None
    assert device.id == data["serial_number"]


def test_register_idempotent(client: TestClient) -> None:
    mac = "aa:bb:cc:dd:ee:ff"
    r1 = client.post("/register", json={"mac_address": mac})
    r2 = client.post("/register", json={"mac_address": mac})
    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r1.json()["serial_number"] == r2.json()["serial_number"]


def test_register_invalid_mac(client: TestClient) -> None:
    response = client.post("/register", json={"mac_address": "not-a-mac"})
    assert response.status_code == 422


def test_register_mac_normalization(client: TestClient, db: Session) -> None:
    client.post("/register", json={"mac_address": "AA:BB:CC:DD:EE:FF"})
    device = db.scalar(select(Device).where(Device.mac_address == "aa:bb:cc:dd:ee:ff"))
    assert device is not None


def test_register_mac_dash_format(client: TestClient, db: Session) -> None:
    client.post("/register", json={"mac_address": "aa-bb-cc-dd-ee-ff"})
    device = db.scalar(select(Device).where(Device.mac_address == "aa:bb:cc:dd:ee:ff"))
    assert device is not None


def test_register_empty_body(client: TestClient) -> None:
    response = client.post("/register", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Ping
# ---------------------------------------------------------------------------


def test_ping_existing_device(client: TestClient, db: Session) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = client.post("/ping", json={"serial_number": serial})
    assert response.status_code == 200
    data = response.json()
    assert data["serial_number"] == serial
    assert data["status"] == "ok"
    assert data["last_ping_at"] is not None

    device = db.get(Device, serial)
    assert device is not None
    assert device.last_ping_at is not None


def test_ping_updates_timestamp(client: TestClient) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    r1 = client.post("/ping", json={"serial_number": serial})
    t1 = datetime.fromisoformat(r1.json()["last_ping_at"])

    r2 = client.post("/ping", json={"serial_number": serial})
    t2 = datetime.fromisoformat(r2.json()["last_ping_at"])

    assert t2 >= t1


def test_ping_unknown_device(client: TestClient) -> None:
    response = client.post("/ping", json={"serial_number": 999999})
    assert response.status_code == 404


def test_ping_invalid_serial(client: TestClient) -> None:
    response = client.post("/ping", json={"serial_number": "abc"})
    assert response.status_code == 422


def test_ping_empty_body(client: TestClient) -> None:
    response = client.post("/ping", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_config_create_keys(client: TestClient, db: Session) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = client.post(
        "/config",
        json={"serial_number": serial, "configs": {"power_mode": "eco", "max_charge": "80"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert sorted(data["updated_keys"]) == ["max_charge", "power_mode"]

    device = db.get(Device, serial)
    assert device is not None
    configs = db.scalars(select(Configuration).where(Configuration.device_id == device.id)).all()
    assert len(configs) == 2


def test_config_update_existing(client: TestClient, db: Session) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    client.post("/config", json={"serial_number": serial, "configs": {"threshold": "50"}})
    client.post("/config", json={"serial_number": serial, "configs": {"threshold": "75"}})

    cfg = db.scalar(select(Configuration).where(Configuration.key == "threshold"))
    assert cfg.value == "75"


def test_config_unknown_device(client: TestClient) -> None:
    response = client.post(
        "/config",
        json={"serial_number": 999999, "configs": {"key": "value"}},
    )
    assert response.status_code == 404


def test_config_empty_configs(client: TestClient) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = client.post("/config", json={"serial_number": serial, "configs": {}})
    assert response.status_code == 422


def test_config_blank_key(client: TestClient) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = client.post("/config", json={"serial_number": serial, "configs": {" ": "value"}})
    assert response.status_code == 422


def test_config_rejects_long_key(client: TestClient) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = client.post(
        "/config",
        json={"serial_number": serial, "configs": {"x" * 256: "value"}},
    )
    assert response.status_code == 422


def test_config_missing_configs(client: TestClient) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = client.post("/config", json={"serial_number": serial})
    assert response.status_code == 422


def test_config_persists_values(client: TestClient, db: Session) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    client.post(
        "/config",
        json={"serial_number": serial, "configs": {"mode": "sleep", "brightness": "10"}},
    )

    device = db.get(Device, serial)
    assert device is not None
    configs = {
        c.key: c.value
        for c in db.scalars(select(Configuration).where(Configuration.device_id == device.id)).all()
    }
    assert configs["mode"] == "sleep"
    assert configs["brightness"] == "10"


def test_config_accepts_scalar_values(client: TestClient, db: Session) -> None:
    reg = client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = client.post(
        "/config",
        json={
            "serial_number": serial,
            "configs": {"max_charge": 80, "safe_mode": True, "voltage": 12.5},
        },
    )
    assert response.status_code == 200

    configs = {
        c.key: c.value
        for c in db.scalars(select(Configuration).where(Configuration.device_id == serial)).all()
    }
    assert configs["max_charge"] == "80"
    assert configs["safe_mode"] == "true"
    assert configs["voltage"] == "12.5"
