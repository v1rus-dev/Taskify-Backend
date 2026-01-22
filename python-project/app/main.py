import logging
import os
import time

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.database import engine
from app.models import Base
from app.routing import routers

def configure_logging() -> None:
    log_file = os.getenv("LOG_FILE", "python-project/app/logs/server.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
        root_logger.addHandler(file_handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.setLevel(logging.INFO)
        if not any(isinstance(h, logging.FileHandler) for h in uvicorn_logger.handlers):
            uvicorn_logger.addHandler(file_handler)


def configure_sentry() -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    environment = os.getenv("SENTRY_ENVIRONMENT", "development")
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0"))
    profiles_sample_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))

    sentry_logging = LoggingIntegration(
        level=logging.ERROR,
        event_level=logging.ERROR,
    )

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        integrations=[FastApiIntegration(), sentry_logging],
    )

app = FastAPI(title="Taskify - Mini Todo API")

configure_logging()
configure_sentry()
logger = logging.getLogger("app")


def _error_response(message: str, code: str, details=None) -> JSONResponse:
    payload = {"error": {"message": message, "code": code}}
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=int(code), content=payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    details = None if isinstance(exc.detail, str) else exc.detail
    return _error_response(message, str(exc.status_code), details)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response("Validation error", "422", exc.errors())


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return _error_response("Internal server error", "500")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    path = request.url.path
    if path not in {"/health", "/admin"}:
        logger.info(
            "HTTP %s %s -> %s (%.2fms)",
            request.method,
            path,
            response.status_code,
            duration_ms,
        )

    return response

@app.on_event("startup")
def create_tables_on_startup() -> None:
    if os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true":
        Base.metadata.create_all(bind=engine)

for router in routers:
    app.include_router(router)
