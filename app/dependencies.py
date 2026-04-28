"""FastAPI dependency injection utilities."""

from app.database import get_session

__all__ = ["get_session"]
