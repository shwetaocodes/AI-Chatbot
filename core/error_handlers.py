import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.exceptions import AppException

logger = logging.getLogger(__name__)


def build_error_response(
    status_code: int,
    error_code: str,
    message: str,
) -> JSONResponse:
    """
    Builds the standard error shape:
    {
        "error": {
            "code": "EMAIL_TAKEN",
            "message": "This email is already registered.",
            "status": 400
        }
    }
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "status": status_code,
            }
        },
    )


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """Handles all AppException subclasses."""
    logger.warning(
        "AppException: %s %s → %s (%d)",
        request.method,
        request.url.path,
        exc.error_code,
        exc.status_code,
    )
    return build_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Overrides FastAPI's default 422 handler.
    Converts Pydantic validation errors into the standard shape.

    Default FastAPI 422:
        {"detail": [{"loc": [...], "msg": "...", "type": "..."}]}

    Our shape:
        {"error": {"code": "VALIDATION_ERROR", "message": "...", "status": 422}}
    """
    errors = exc.errors()

    first = errors[0]
    field = " → ".join(str(loc) for loc in first["loc"] if loc != "body")
    message = f"{field}: {first['msg']}" if field else first["msg"]

    logger.warning(
        "ValidationError: %s %s → %s",
        request.method,
        request.url.path,
        message,
    )

    return build_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message=message,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catches any unhandled exception and returns a clean 500.
    Prevents raw Python tracebacks leaking to clients.
    """
    logger.error(
        "Unhandled exception: %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
    )
