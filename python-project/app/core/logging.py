import base64
import binascii
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any

from fastapi import FastAPI, Request

from app.core.security import decode_access_token

REQUEST_LOG_FIELDS = (
    "request_id",
    "actor_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "client_ip",
    "user_agent",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, "service", "unknown"),
        }

        for field in REQUEST_LOG_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


class ServiceNameFilter(logging.Filter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "service"):
            record.service = self.service_name
        return True


def _strtobool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def configure_logging(service_name: str, log_file: str) -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    use_json = _strtobool(os.getenv("LOG_JSON", "true"))

    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    formatter_name = "json" if use_json else "plain"

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {"()": "app.core.logging.JsonFormatter"},
                "plain": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": formatter_name,
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": log_level,
                    "formatter": formatter_name,
                    "filename": log_file,
                    "encoding": "utf-8",
                },
            },
            "root": {"level": log_level, "handlers": ["console", "file"]},
        }
    )

    service_filter = ServiceNameFilter(service_name)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(service_filter)


def _decode_basic_auth_username(value: str) -> str | None:
    try:
        decoded = base64.b64decode(value).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None

    username, separator, _ = decoded.partition(":")
    if not separator or not username:
        return None
    return username


def _get_request_session(request: Request) -> dict[str, Any] | None:
    try:
        session = request.session
    except Exception:
        return None

    if isinstance(session, dict):
        return session
    return None


def extract_actor_id(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization:
        scheme, _, credentials = authorization.partition(" ")
        scheme = scheme.lower()
        credentials = credentials.strip()

        if scheme == "bearer" and credentials:
            try:
                payload = decode_access_token(credentials)
                subject = payload.get("sub")
                if subject:
                    return str(subject)
            except ValueError:
                pass

        if scheme == "basic" and credentials:
            username = _decode_basic_auth_username(credentials)
            if username:
                return f"admin:{username}"

    state_actor = getattr(request.state, "admin_actor", None)
    if state_actor:
        return str(state_actor)

    session = _get_request_session(request)
    if session:
        admin_actor = session.get("admin_actor")
        if admin_actor:
            return str(admin_actor)

    return "anonymous"


def extract_request_id(request: Request) -> str:
    request_id = request.headers.get("x-request-id")
    if request_id:
        return request_id
    return str(uuid.uuid4())


def extract_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def build_request_log_payload(
    request: Request,
    service_name: str,
    request_id: str,
    actor_id: str,
    status_code: int,
    duration_ms: float,
) -> dict[str, Any]:
    return {
        "service": service_name,
        "request_id": request_id,
        "actor_id": actor_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "client_ip": extract_client_ip(request),
        "user_agent": request.headers.get("user-agent", ""),
    }


def register_request_logging(
    app: FastAPI, service_name: str, logger_name: str
) -> None:
    logger = logging.getLogger(logger_name)

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = extract_request_id(request)
        actor_id = extract_actor_id(request)
        request.state.request_id = request_id
        request.state.actor_id = actor_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "Request failed",
                extra=build_request_log_payload(
                    request=request,
                    service_name=service_name,
                    request_id=request_id,
                    actor_id=actor_id,
                    status_code=500,
                    duration_ms=duration_ms,
                ),
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request handled",
            extra=build_request_log_payload(
                request=request,
                service_name=service_name,
                request_id=request_id,
                actor_id=actor_id,
                status_code=response.status_code,
                duration_ms=duration_ms,
            ),
        )
        return response
