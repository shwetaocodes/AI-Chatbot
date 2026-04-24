import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with method, path, status code, and duration.

    Output format:
        INFO: POST /auth/login → 200 (45ms)
        INFO: GET  /users/me  → 401 (12ms)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000

        log_fn = (
            logger.warning
            if response.status_code >= 400
            else logger.info
        )

        log_fn(
            "%-6s %-40s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        return response