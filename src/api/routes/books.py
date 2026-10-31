from fastapi import APIRouter, HTTPException
from src.database.repositories.book_repository import BookRepository
from src.database.repositories.scan_repository import ScanRepository

router = APIRouter()
book_repository = BookRepository()
scan_repository = ScanRepository()

# get endpoints==============================================
@router.get("/books")
def get_all_books():
    return book_repository.get_all()

@router.get("/books/{book_id}")
def get_one_book(book_id: int):
    book = book_repository.get_by_id(book_id)
    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )
    return book

@router.get("/scans/{scan_id}/books")
def get_books_by_scan(scan_id: int):
    if scan_repository.get_by_id(scan_id) is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    return book_repository.get_by_scan(scan_id)







