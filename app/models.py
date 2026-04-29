"""SQLAlchemy 2.0 declarative models."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Device(Base):
    """A registered moonBattery device."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mac_address: Mapped[str] = mapped_column(
        String(17), unique=True, nullable=False, index=True
    )
    last_ping_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
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
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
