"""Rate limiting for expensive API requests."""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    headers_enabled=True,
    retry_after="delta-seconds",
)


def rate_limit_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    limited_response = _rate_limit_exceeded_handler(request, exc)

    # Preserve rate-limit headers while rebuilding the JSON body.
    headers = {
        name: value
        for name, value in limited_response.headers.items()
        if name.lower() not in {"content-length", "content-type"}
    }

    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                "Scan limit reached. Please wait before trying again."
            ),
        },
        headers=headers,
    )