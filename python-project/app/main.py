import logging
import os
import time

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


app = FastAPI(title="Taskify - Mini Todo API")

configure_logging()
logger = logging.getLogger("app")


def _error_response(message: str, code: str, details=None, status_code: int | None = None) -> JSONResponse:
    payload = {"error": {"message": message, "code": code}}
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code or 500, content=payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
        message = exc.detail["message"]
        code = exc.detail["code"]
        details = exc.detail.get("details")
    else:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        code = "HTTP_ERROR"
        details = None if isinstance(exc.detail, str) else exc.detail
    return _error_response(message, code, details, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response("Validation error", "VALIDATION_ERROR", exc.errors(), status_code=422)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return _error_response("Internal server error", "INTERNAL_ERROR", status_code=500)


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
