"""Tests for the /config endpoint."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Configuration, Device


@pytest.mark.asyncio
async def test_config_create_new_keys(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Creating new config keys should return updated keys list."""
    reg = await async_client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = await async_client.post(
        "/config",
        json={"serial_number": serial, "configs": {"power_mode": "eco", "max_charge": "80"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert sorted(data["updated_keys"]) == ["max_charge", "power_mode"]

    # Verify in DB
    result = await db_session.execute(
        select(Configuration).where(Configuration.device_id == 1)
    )
    configs = result.scalars().all()
    assert len(configs) == 2
    keys = {c.key for c in configs}
    assert keys == {"power_mode", "max_charge"}


@pytest.mark.asyncio
async def test_config_update_existing_keys(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Updating an existing key should change its value."""
    reg = await async_client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    await async_client.post(
        "/config",
        json={"serial_number": serial, "configs": {"threshold": "50"}},
    )

    response = await async_client.post(
        "/config",
        json={"serial_number": serial, "configs": {"threshold": "75"}},
    )
    assert response.status_code == 200

    result = await db_session.execute(
        select(Configuration).where(Configuration.key == "threshold")
    )
    config = result.scalar_one()
    assert config.value == "75"


@pytest.mark.asyncio
async def test_config_mixed_insert_update(async_client: AsyncClient) -> None:
    """A mix of new and existing keys should all be handled."""
    reg = await async_client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    await async_client.post(
        "/config",
        json={"serial_number": serial, "configs": {"existing": "1"}},
    )

    response = await async_client.post(
        "/config",
        json={"serial_number": serial, "configs": {"existing": "2", "new_key": "3"}},
    )
    data = response.json()
    assert sorted(data["updated_keys"]) == ["existing", "new_key"]


@pytest.mark.asyncio
async def test_config_unknown_device(async_client: AsyncClient) -> None:
    """Config for a non-existent serial should return 404."""
    response = await async_client.post(
        "/config",
        json={"serial_number": 999999, "configs": {"key": "value"}},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_config_empty_configs(async_client: AsyncClient) -> None:
    """An empty configs dict should return 422."""
    reg = await async_client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = await async_client.post(
        "/config",
        json={"serial_number": serial, "configs": {}},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_config_missing_configs(async_client: AsyncClient) -> None:
    """A request without configs should return 422."""
    reg = await async_client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    response = await async_client.post("/config", json={"serial_number": serial})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_config_persists_values(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Config values should be retrievable from the database."""
    reg = await async_client.post("/register", json={"mac_address": "aa:bb:cc:dd:ee:ff"})
    serial = reg.json()["serial_number"]

    await async_client.post(
        "/config",
        json={"serial_number": serial, "configs": {"mode": "sleep", "brightness": "10"}},
    )

    result = await db_session.execute(select(Device).where(Device.serial_number == serial))
    device = result.scalar_one()

    result = await db_session.execute(
        select(Configuration).where(Configuration.device_id == device.id)
    )
    configs = {c.key: c.value for c in result.scalars().all()}
    assert configs["mode"] == "sleep"
    assert configs["brightness"] == "10"
