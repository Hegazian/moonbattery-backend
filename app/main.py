"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="moonBattery IoT Backend",
    description="REST API for moonBattery devices.",
    version="0.1.0",
    lifespan=lifespan,
)

from app.api import router  # noqa: E402

app.include_router(router)
