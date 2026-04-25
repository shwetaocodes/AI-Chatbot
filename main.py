from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.auth import router as auth_router
from api.health import router as health_router
from api.users import router as users_router
from core.error_handlers import (
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from core.exceptions import AppException
from core.middleware import RequestLoggingMiddleware

app = FastAPI(
    title="Chatbot API",
    version="0.1.0",
    description="Backend API for AI Chatbot",
)

app.add_middleware(RequestLoggingMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "API working"}
