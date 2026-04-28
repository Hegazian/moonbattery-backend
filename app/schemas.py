"""Pydantic request and response schemas."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    """Request body for device registration."""

    mac_address: str = Field(..., min_length=17, max_length=17)

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v: str) -> str:
        """Normalize and validate MAC address format."""
        # Replace dashes with colons for normalization
        normalized = v.lower().replace("-", ":")
        if not re.fullmatch(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", normalized):
            raise ValueError("Invalid MAC address format. Expected XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX")
        return normalized


class RegisterResponse(BaseModel):
    """Response body for successful device registration."""

    serial_number: int
    mac_address: str
    created_at: datetime


class PingRequest(BaseModel):
    """Request body for device heartbeat ping."""

    serial_number: int = Field(..., gt=0)


class PingResponse(BaseModel):
    """Response body for successful device ping."""

    serial_number: int
    last_ping_at: datetime
    status: str = "ok"


class ConfigRequest(BaseModel):
    """Request body for configuration update."""

    serial_number: int = Field(..., gt=0)
    configs: dict[str, str] = Field(..., min_length=1)

    @field_validator("configs")
    @classmethod
    def validate_configs(cls, v: dict[str, str]) -> dict[str, str]:
        """Ensure configs dict is not empty."""
        if not v:
            raise ValueError("configs must contain at least one key-value pair")
        return v


class ConfigResponse(BaseModel):
    """Response body for successful configuration update."""

    serial_number: int
    updated_keys: list[str]
    status: str = "ok"
