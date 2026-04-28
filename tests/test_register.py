"""Tests for the /register endpoint."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device


@pytest.mark.asyncio
async def test_register_new_device(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """A valid MAC address should create a new device with a serial number."""
    response = await async_client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    assert response.status_code == 201
    data = response.json()
    assert "serial_number" in data
    assert data["mac_address"] == "aa:bb:cc:dd:ee:ff"
    assert data["created_at"] is not None

    # Verify in DB
    result = await db_session.execute(select(Device).where(Device.mac_address == "aa:bb:cc:dd:ee:ff"))
    device = result.scalar_one()
    assert device.serial_number == data["serial_number"]


@pytest.mark.asyncio
async def test_register_idempotent(async_client: AsyncClient) -> None:
    """Re-registering the same MAC should return the existing serial."""
    mac = "aa:bb:cc:dd:ee:ff"
    r1 = await async_client.post("/register", json={"mac_address": mac})
    assert r1.status_code == 201
    serial_1 = r1.json()["serial_number"]

    r2 = await async_client.post("/register", json={"mac_address": mac})
    assert r2.status_code == 201
    serial_2 = r2.json()["serial_number"]

    assert serial_1 == serial_2


@pytest.mark.asyncio
async def test_register_invalid_mac_format(async_client: AsyncClient) -> None:
    """An invalid MAC format should return 422."""
    response = await async_client.post("/register", json={"mac_address": "not-a-mac"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_mac_normalization(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Uppercase MAC should be normalized to lowercase."""
    response = await async_client.post("/register", json={"mac_address": "AA:BB:CC:DD:EE:FF"})
    assert response.status_code == 201

    result = await db_session.execute(select(Device).where(Device.mac_address == "aa:bb:cc:dd:ee:ff"))
    device = result.scalar_one()
    assert device.mac_address == "aa:bb:cc:dd:ee:ff"


@pytest.mark.asyncio
async def test_register_mac_dash_format(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Dash-separated MAC should be accepted and normalized to colons."""
    response = await async_client.post("/register", json={"mac_address": "aa-bb-cc-dd-ee-ff"})
    assert response.status_code == 201

    result = await db_session.execute(select(Device).where(Device.mac_address == "aa:bb:cc:dd:ee:ff"))
    device = result.scalar_one()
    assert device.mac_address == "aa:bb:cc:dd:ee:ff"


@pytest.mark.asyncio
async def test_register_empty_body(async_client: AsyncClient) -> None:
    """An empty request body should return 422."""
    response = await async_client.post("/register", json={})
    assert response.status_code == 422
