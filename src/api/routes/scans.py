from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from PIL import Image, ImageOps, UnidentifiedImageError

from src.database.repositories.scan_repository import ScanRepository
from src.services.scan_service import process_scan
from src.api.rate_limiting import limiter
from src.config import SCAN_RATE_LIMIT

router = APIRouter()
scan_repository = ScanRepository()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_PIXELS = 20_000_000

# get (Retrieval) endpoints==============================================
@router.get("/scans")
def get_all_scans():
    return scan_repository.get_all()


@router.get("/scans/{scan_id}")
def get_one_scan(scan_id: int):
    scan = scan_repository.get_by_id(scan_id)

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found"
        )

    return scan

# post (Creation) endpoints==============================================
@router.post("/scans", status_code=201)
@limiter.limit(SCAN_RATE_LIMIT)
def create_scan(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
):
    contents = file.file.read(MAX_UPLOAD_BYTES + 1)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="The image must be 10 MB or smaller.",
        )

    # Read the actual image contents, rather than trusting its filename.
    try:
        with Image.open(BytesIO(contents)) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise HTTPException(
                    status_code=415,
                    detail="Upload a JPEG or PNG image.",
                )

            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=413,
                    detail="The image must be 20 megapixels or smaller.",
                )

            # Correct phone-photo orientation and normalize to JPEG.
            normalized_image = ImageOps.exif_transpose(image).convert("RGB")

    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail="The file could not be read as an image.",
        ) from exc

    image_path = UPLOAD_DIR / f"{uuid4().hex}.jpg"

    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        normalized_image.save(image_path, format="JPEG", quality=90)

        return process_scan(image_path)

    except Exception:
        # Remove the uploaded image if processing or saving fails.
        image_path.unlink(missing_ok=True)
        raise

    finally:
        normalized_image.close()
