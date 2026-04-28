"""Registration endpoint router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.schemas import RegisterRequest, RegisterResponse
from app.services import DuplicateDeviceError, register_device

router = APIRouter(tags=["Registration"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new moonBattery device",
)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> RegisterResponse:
    """Register a device by its MAC address.

    If the MAC is already registered, returns the existing device (idempotent).
    """
    try:
        device = await register_device(request.mac_address, session)
    except DuplicateDeviceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    assert device.serial_number is not None
    assert device.created_at is not None
    return RegisterResponse(
        serial_number=device.serial_number,
        mac_address=device.mac_address,
        created_at=device.created_at,
    )
