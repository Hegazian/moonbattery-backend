"""Configuration endpoint router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.schemas import ConfigRequest, ConfigResponse
from app.services import DeviceNotFoundError, update_device_config

router = APIRouter(tags=["Configuration"])


@router.post(
    "/config",
    response_model=ConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Update device configuration key-value pairs",
)
async def update_config(
    request: ConfigRequest,
    session: AsyncSession = Depends(get_session),
) -> ConfigResponse:
    """Synchronize one or more configuration key-value pairs for a device."""
    try:
        updated_keys = await update_device_config(
            request.serial_number, request.configs, session
        )
    except DeviceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ConfigResponse(
        serial_number=request.serial_number,
        updated_keys=updated_keys,
    )
