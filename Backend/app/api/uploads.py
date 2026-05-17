import os
from pathlib import Path
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from PIL import Image

from app.core.config import get_settings

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


def _compress_and_save_image(file_path: Path, max_size: tuple[int, int] = (256, 256)) -> Path:
    try:
        with Image.open(file_path) as img:
            image = img.convert("RGB")
            image.thumbnail(max_size)
            output_path = file_path.with_suffix(".webp")
            image.save(output_path, format="WEBP", optimize=True, quality=70, method=6)
            if output_path != file_path:
                file_path.unlink(missing_ok=True)
            return output_path
    except Exception:
        pass  # Ignore compression errors and use original
    return file_path


@router.post("")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")

    settings = get_settings()
    uploads_dir = settings.uploads_filesystem_path()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Check file size (approximate by reading)
    contents = await file.read()
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    # Save file
    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    if not ext:
        ext = ".png"

    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = uploads_dir / filename

    with open(file_path, "wb") as f:
        f.write(contents)

    file_path = _compress_and_save_image(file_path)
    filename = file_path.name

    uploads_path = settings.uploads_url_path()
    return {"url": f"/{uploads_path}/{filename}", "path": f"/{uploads_path}/{filename}"}
