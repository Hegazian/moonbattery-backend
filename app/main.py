"""FastAPI application factory and lifespan management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.database import engine
from app.models import SQLModel
from app.routers import config, ping, register
from app.services import DeviceNotFoundError, DuplicateDeviceError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: create tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="moonBattery IoT Backend",
    description="REST API for registering, pinging, and configuring moonBattery devices.",
    version="0.1.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(register.router)
app.include_router(ping.router)
app.include_router(config.router)


@app.exception_handler(DeviceNotFoundError)
async def device_not_found_handler(request: object, exc: DeviceNotFoundError) -> JSONResponse:
    """Return 404 for unknown devices."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateDeviceError)
async def duplicate_device_handler(request: object, exc: DuplicateDeviceError) -> JSONResponse:
    """Return 409 for duplicate MAC registration attempts."""
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: object, exc: IntegrityError) -> JSONResponse:
    """Return 409 for database integrity violations."""
    return JSONResponse(
        status_code=409,
        content={"detail": "Conflict with existing resource."},
    )
