"""SQLAlchemy 2.0 declarative models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Device(Base):
    """A registered moonBattery device."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mac_address: Mapped[str] = mapped_column(
        String(17), unique=True, nullable=False, index=True
    )
    serial_number: Mapped[int | None] = mapped_column(
        Integer, unique=True, nullable=True, index=True
    )
    last_ping_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class Configuration(Base):
    """A key-value configuration pair for a device."""

    __tablename__ = "configurations"
    __table_args__ = (UniqueConstraint("device_id", "key", name="uix_device_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
