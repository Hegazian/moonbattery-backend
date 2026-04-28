"""SQLModel table definitions for moonBattery backend."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class Device(SQLModel, table=True):
    """Represents a registered moonBattery device."""

    __tablename__ = "devices"

    id: int | None = Field(default=None, primary_key=True)
    mac_address: str = Field(
        sa_column=Column(String(17), unique=True, nullable=False, index=True)
    )
    serial_number: int | None = Field(
        default=None,
        sa_column=Column(Integer, unique=True, nullable=True, index=True),
    )
    last_ping_at: datetime | None = Field(default=None)
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, nullable=False, server_default=func.now()),
    )


class Configuration(SQLModel, table=True):
    """Represents a key-value configuration pair for a device."""

    __tablename__ = "configurations"
    __table_args__ = (UniqueConstraint("device_id", "key", name="uix_device_key"),)

    id: int | None = Field(default=None, primary_key=True)
    device_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
        )
    )
    key: str = Field(sa_column=Column(String(255), nullable=False))
    value: str = Field(sa_column=Column(String, nullable=False))
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, nullable=False, server_default=func.now()),
    )
