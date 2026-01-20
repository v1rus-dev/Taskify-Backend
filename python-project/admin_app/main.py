import logging
import os

from fastapi import FastAPI

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
app.include_router(admin_router)
