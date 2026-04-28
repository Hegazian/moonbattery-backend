"""Ping endpoint router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.schemas import PingRequest, PingResponse
from app.services import DeviceNotFoundError, ping_device

router = APIRouter(tags=["Heartbeat"])


@router.post(
    "/ping",
    response_model=PingResponse,
    status_code=status.HTTP_200_OK,
    summary="Record a device heartbeat ping",
)
async def ping(
    request: PingRequest,
    session: AsyncSession = Depends(get_session),
) -> PingResponse:
    """Record a heartbeat ping for a device and update its last contact time."""
    try:
        device = await ping_device(request.serial_number, session)
    except DeviceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    assert device.serial_number is not None
    assert device.last_ping_at is not None
    return PingResponse(
        serial_number=device.serial_number,
        last_ping_at=device.last_ping_at,
    )
