# python -m uvicorn src.api.main:app --reload
# Define API endpoints for scans, books, and recommendations
from slowapi.errors import RateLimitExceeded
from src.api.rate_limiting import limiter, rate_limit_handler
from fastapi import FastAPI
from src.api.routes import books, recommendations, scans

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_handler,
)

app.include_router(scans.router, tags=["Scans"])
app.include_router(books.router, tags=["Books"])
app.include_router(recommendations.router, tags=["Recommendations"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "Hello, World!"}


