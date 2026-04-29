"""API endpoints and Pydantic schemas for moonBattery backend."""

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Configuration, Device

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    mac_address: str = Field(..., min_length=17, max_length=17)

    @field_validator("mac_address")
    @classmethod
    def _validate_mac(cls, v: str) -> str:
        normalized = v.lower().replace("-", ":")
        if not re.fullmatch(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", normalized):
            raise ValueError("Invalid MAC address format")
        return normalized


class RegisterResponse(BaseModel):
    serial_number: int
    mac_address: str
    created_at: datetime


class PingRequest(BaseModel):
    serial_number: int = Field(..., gt=0)


class PingResponse(BaseModel):
    serial_number: int
    last_ping_at: datetime
    status: str = "ok"


class ConfigRequest(BaseModel):
    serial_number: int = Field(..., gt=0)
    configs: dict[str, str] = Field(..., min_length=1)


class ConfigResponse(BaseModel):
    serial_number: int
    updated_keys: list[str]
    status: str = "ok"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    """Register a device by MAC address. Returns existing device if MAC already registered."""
    existing = db.scalar(select(Device).where(Device.mac_address == request.mac_address))
    if existing:
        return RegisterResponse(
            serial_number=existing.serial_number,
            mac_address=existing.mac_address,
            created_at=existing.created_at,
        )

    device = Device(mac_address=request.mac_address)
    db.add(device)
    db.commit()
    db.refresh(device)

    # Use id as serial_number for simplicity (guaranteed unique, auto-increment)
    if device.serial_number is None:
        device.serial_number = device.id
        db.commit()
        db.refresh(device)

    return RegisterResponse(
        serial_number=device.serial_number,
        mac_address=device.mac_address,
        created_at=device.created_at,
    )


@router.post("/ping", response_model=PingResponse)
def ping(request: PingRequest, db: Session = Depends(get_db)) -> PingResponse:
    """Record a heartbeat ping and update last contact time."""
    device = db.scalar(select(Device).where(Device.serial_number == request.serial_number))
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device.last_ping_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(device)

    return PingResponse(
        serial_number=device.serial_number,
        last_ping_at=device.last_ping_at,
    )


@router.post("/config", response_model=ConfigResponse)
def update_config(request: ConfigRequest, db: Session = Depends(get_db)) -> ConfigResponse:
    """Synchronize one or more configuration key-value pairs for a device."""
    device = db.scalar(select(Device).where(Device.serial_number == request.serial_number))
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    updated_keys: list[str] = []
    for key, value in request.configs.items():
        config = db.scalar(
            select(Configuration).where(
                Configuration.device_id == device.id, Configuration.key == key
            )
        )
        if config:
            config.value = value
        else:
            db.add(Configuration(device_id=device.id, key=key, value=value))
        updated_keys.append(key)

    db.commit()
    return ConfigResponse(serial_number=request.serial_number, updated_keys=updated_keys)
