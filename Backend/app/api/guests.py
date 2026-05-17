from fastapi import APIRouter, HTTPException, status

from app.schemas.guest import GuestProfileCreate, GuestProfileRead, GuestProfileUpdate

router = APIRouter(prefix="/api/guests", tags=["guests"])


@router.post("/profile", response_model=GuestProfileRead, status_code=status.HTTP_201_CREATED)
def create_guest_profile(payload: GuestProfileCreate) -> GuestProfileRead:
    return GuestProfileRead(**payload.model_dump())


@router.put("/{guest_id}/profile", response_model=GuestProfileRead)
def update_guest_profile(guest_id: str, payload: GuestProfileUpdate) -> GuestProfileRead:
    payload_guest_id = payload.guest_id.strip() if payload.guest_id else guest_id.strip()
    if not payload_guest_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Guest id is required")
    if payload.guest_id and payload_guest_id != guest_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Guest id mismatch")
    return GuestProfileRead(guest_id=payload_guest_id, **payload.model_dump(exclude={"guest_id"}))
