from fastapi import APIRouter, HTTPException
from src.database.repositories.scan_repository import ScanRepository
from src.api.schemas import ScanCreate

router = APIRouter()
scan_repository = ScanRepository()


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
def create_scan(scan: ScanCreate):
    scan_id = scan_repository.create(scan.image_path)
    return {"scan_id": scan_id}
