from fastapi import APIRouter, HTTPException
from src.config import EMBEDDING_MODEL_NAME
from src.database.repositories.recommendation_repository import RecommendationResultRepository
from src.api.schemas import RecommendationCreate
from src.database.repositories.book_repository import BookRepository
from src.database.repositories.scan_repository import ScanRepository
from src.services.recommendation_service import recommend_books

router = APIRouter()
recommendation_repository = RecommendationResultRepository()
scan_repository = ScanRepository()
book_repository = BookRepository()

# get endpoints==============================================
@router.get("/recommendations")
def get_all_recommendations():
    return recommendation_repository.get_all()

@router.get("/recommendations/{result_id}")
def get_one_recommendation(result_id: int):
    result = recommendation_repository.get_by_id(result_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recommendation result not found"
        )
    return result

@router.get("/scans/{scan_id}/recommendations")
def get_recommendations_by_scan(scan_id: int):
    if scan_repository.get_by_id(scan_id) is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    return recommendation_repository.get_by_scan_id(scan_id)

# post endpoints==============================================
@router.post("/scans/{scan_id}/recommendations", status_code=201)
def create_recommendation(
    scan_id: int,
    request: RecommendationCreate,
):
    if scan_repository.get_by_id(scan_id) is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    books = book_repository.get_by_scan(scan_id)

    ranked_outcome = recommend_books(
        books,
        request.preference_text,
        top_k=request.top_k,
        model_name=EMBEDDING_MODEL_NAME,
    )

    result_id = recommendation_repository.create(
        scan_id=scan_id,
        model_name=EMBEDDING_MODEL_NAME,
        preference_text=request.preference_text,
        top_k=request.top_k,
        ranked_outcome=ranked_outcome,
    )

    return {
        "result_id": result_id,
        "scan_id": scan_id,
        "recommendations": ranked_outcome,
    }

