import os
from pathlib import Path
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from PIL import Image

from app.api.openapi import error_response
from app.core.config import get_settings
from app.schemas.common import UploadResponse

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


def _compress_and_save_image(
    file_path: Path,
    max_size: tuple[int, int] = (256, 256),
    quality: int = 70,
) -> Path:
    try:
        with Image.open(file_path) as img:
            image = img.convert("RGB")
            image.thumbnail(max_size)
            for suffix, save_kwargs in (
                (".webp", {"format": "WEBP", "optimize": True, "quality": quality, "method": 6}),
                (".jpg", {"format": "JPEG", "optimize": True, "quality": quality}),
            ):
                output_path = file_path.with_suffix(suffix)
                try:
                    image.save(output_path, **save_kwargs)
                except Exception:
                    output_path.unlink(missing_ok=True)
                    continue
                if output_path != file_path:
                    file_path.unlink(missing_ok=True)
                return output_path
    except Exception:
        pass  # Ignore compression errors and use original
    return file_path


@router.post(
    "",
    response_model=UploadResponse,
    summary="Upload image asset",
    description=(
        "Uploads an image, stores it in the configured uploads directory, and attempts server-side "
        "compression to WEBP or JPEG. The returned path can be used in board and guest profile payloads."
    ),
    responses={
        400: error_response("The uploaded file is not an image.", "File must be an image"),
        413: error_response("The uploaded image exceeds the configured maximum size.", "File too large"),
        422: error_response("Multipart payload validation failed.", "Field required"),
    },
)
async def upload_image(file: UploadFile = File(..., description="Image file to upload.")) -> UploadResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")

    settings = get_settings()
    uploads_dir = settings.uploads_filesystem_path()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    contents = await file.read()

    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    if not ext:
        ext = ".png"

    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = uploads_dir / filename

    with open(file_path, "wb") as f:
        f.write(contents)

    file_path = _compress_and_save_image(file_path)
    if file_path.stat().st_size > settings.max_upload_size_bytes:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    filename = file_path.name

    uploads_path = settings.uploads_url_path()
    return {"url": f"/{uploads_path}/{filename}", "path": f"/{uploads_path}/{filename}"}
