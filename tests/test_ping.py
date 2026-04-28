"""Tests for the /ping endpoint."""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device


@pytest.mark.asyncio
async def test_ping_existing_device(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Ping should update last_ping_at for an existing device."""
    # Register a device first
    reg = await async_client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = await async_client.post("/ping", json={"serial_number": serial})
    assert response.status_code == 200
    data = response.json()
    assert data["serial_number"] == serial
    assert data["status"] == "ok"
    assert data["last_ping_at"] is not None

    # Verify in DB
    result = await db_session.execute(select(Device).where(Device.serial_number == serial))
    device = result.scalar_one()
    assert device.last_ping_at is not None


@pytest.mark.asyncio
async def test_ping_updates_timestamp(async_client: AsyncClient) -> None:
    """Two consecutive pings should show increasing timestamps."""
    reg = await async_client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    r1 = await async_client.post("/ping", json={"serial_number": serial})
    t1 = datetime.fromisoformat(r1.json()["last_ping_at"].replace("Z", "+00:00"))

    r2 = await async_client.post("/ping", json={"serial_number": serial})
    t2 = datetime.fromisoformat(r2.json()["last_ping_at"].replace("Z", "+00:00"))

    assert t2 >= t1


@pytest.mark.asyncio
async def test_ping_unknown_device(async_client: AsyncClient) -> None:
    """Ping for a non-existent serial should return 404."""
    response = await async_client.post("/ping", json={"serial_number": 999999})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ping_invalid_serial(async_client: AsyncClient) -> None:
    """A string serial should return 422."""
    response = await async_client.post("/ping", json={"serial_number": "abc"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ping_missing_serial(async_client: AsyncClient) -> None:
    """An empty body should return 422."""
    response = await async_client.post("/ping", json={})
    assert response.status_code == 422
