"""Business logic services for moonBattery backend."""

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Configuration, Device


class DeviceNotFoundError(Exception):
    """Raised when a device lookup by serial number fails."""

    def __init__(self, serial_number: int) -> None:
        self.serial_number = serial_number
        super().__init__(f"Device with serial number {serial_number} not found.")


class DuplicateDeviceError(Exception):
    """Raised when attempting to register a device with an existing MAC."""

    def __init__(self, mac_address: str) -> None:
        self.mac_address = mac_address
        super().__init__(f"Device with MAC address {mac_address} is already registered.")


async def register_device(mac_address: str, session: AsyncSession) -> Device:
    """Register a new device or return existing one if MAC already exists.

    Args:
        mac_address: Normalized MAC address string.
        session: Async database session.

    Returns:
        The registered (or existing) Device instance.

    Raises:
        DuplicateDeviceError: If the MAC is already registered (unexpected race condition).
    """
    # Check for existing device
    stmt = select(Device).where(Device.mac_address == mac_address)  # type: ignore[arg-type]
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # Insert new device — use id as serial_number for cross-DB compatibility
    device = Device(mac_address=mac_address)
    session.add(device)
    await session.commit()
    await session.refresh(device)
    if device.serial_number is None:
        device.serial_number = device.id
        await session.commit()
        await session.refresh(device)
    return device


async def ping_device(serial_number: int, session: AsyncSession) -> Device:
    """Record a heartbeat ping for a device.

    Args:
        serial_number: The device's serial number.
        session: Async database session.

    Returns:
        The updated Device instance.

    Raises:
        DeviceNotFoundError: If no device matches the serial number.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stmt = (
        update(Device)
        .where(Device.serial_number == serial_number)  # type: ignore[arg-type]
        .values(last_ping_at=now)
        .returning(Device)
    )
    result = await session.execute(stmt)
    device = result.scalar_one_or_none()
    if not device:
        raise DeviceNotFoundError(serial_number)
    await session.commit()
    return device


async def update_device_config(
    serial_number: int, configs: dict[str, str], session: AsyncSession
) -> list[str]:
    """Upsert configuration key-value pairs for a device.

    Args:
        serial_number: The device's serial number.
        configs: Dictionary of configuration key-value pairs.
        session: Async database session.

    Returns:
        List of keys that were updated.

    Raises:
        DeviceNotFoundError: If no device matches the serial number.
    """
    # Verify device exists
    stmt = select(Device.id).where(Device.serial_number == serial_number)  # type: ignore[call-overload]
    result = await session.execute(stmt)
    device_id = result.scalar_one_or_none()
    if device_id is None:
        raise DeviceNotFoundError(serial_number)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    updated_keys: list[str] = []

    for key, value in configs.items():
        upsert_stmt = (
            insert(Configuration)
            .values(device_id=device_id, key=key, value=value, updated_at=now)
            .on_conflict_do_update(
                index_elements=["device_id", "key"],
                set_={"value": value, "updated_at": now},
            )
        )
        await session.execute(upsert_stmt)
        updated_keys.append(key)

    await session.commit()
    return updated_keys
