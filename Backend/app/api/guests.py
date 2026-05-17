from fastapi import APIRouter, HTTPException, Path, status

from app.api.openapi import error_response
from app.schemas.guest import GuestProfileCreate, GuestProfileRead, GuestProfileUpdate

router = APIRouter(prefix="/api/guests", tags=["guests"])


@router.post(
    "/profile",
    response_model=GuestProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create guest profile payload",
    description=(
        "Creates a guest profile payload used by the frontend for collaborative presence. "
        "The current implementation is stateless and echoes normalized data."
    ),
    responses={422: error_response("Validation failed for the guest profile payload.", "Guest id is required")},
)
def create_guest_profile(payload: GuestProfileCreate) -> GuestProfileRead:
    return GuestProfileRead(**payload.model_dump())


@router.put(
    "/{guest_id}/profile",
    response_model=GuestProfileRead,
    summary="Update guest profile payload",
    description=(
        "Updates a guest profile payload. When `guest_id` is also provided in the request body, "
        "it must match the path parameter."
    ),
    responses={
        422: error_response("Guest id validation failed or the path and body values do not match.", "Guest id mismatch")
    },
)
def update_guest_profile(
    payload: GuestProfileUpdate = ...,
    guest_id: str = Path(description="Guest identifier to update.", examples=["guest-42"]),
) -> GuestProfileRead:
    payload_guest_id = payload.guest_id.strip() if payload.guest_id else guest_id.strip()
    if not payload_guest_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Guest id is required")
    if payload.guest_id and payload_guest_id != guest_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Guest id mismatch")
    return GuestProfileRead(guest_id=payload_guest_id, **payload.model_dump(exclude={"guest_id"}))
