import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from app.routing.admin import router as admin_router


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


app = FastAPI(title="Taskify Admin")
configure_logging()
logger = logging.getLogger("admin_app")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "HTTP %s %s -> %s (%.2fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/", include_in_schema=False)
def _root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/admin", status_code=302)


app.include_router(admin_router)
