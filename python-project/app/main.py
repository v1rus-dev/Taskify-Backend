import logging
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import INTERNAL_ALERTS_API_KEY
from app.core.logging import configure_logging, register_request_logging
from app.database import engine
from app.models import Base
from app.routing import routers
from app.services.telegram_alerts import CriticalAlert, TelegramAlertsClient

app = FastAPI(title="Taskify - Mini Todo API")
configure_logging(service_name="api", log_file=os.getenv("LOG_FILE", "python-project/app/logs/api.log"))
register_request_logging(app, service_name="api", logger_name="app.request")
logger = logging.getLogger("app")
alerts_client = TelegramAlertsClient()


class CriticalAlertRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=4000)
    source: str = Field(default="taskify-backend", min_length=1, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=10)
    details: dict[str, Any] | None = None


def _error_response(
    message: str,
    code: str,
    details: Any | None = None,
    status_code: int | None = None,
) -> JSONResponse:
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


@app.on_event("startup")
def create_tables_on_startup() -> None:
    if os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true":
        Base.metadata.create_all(bind=engine)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await alerts_client.close()


for router in routers:
    app.include_router(router)


@app.post("/internal/alerts/critical", tags=["Internal"])
async def send_critical_alert(
    payload: CriticalAlertRequest,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    if INTERNAL_ALERTS_API_KEY and x_internal_key != INTERNAL_ALERTS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_INTERNAL_KEY", "message": "Invalid internal key"},
        )

    result = await alerts_client.send_critical_alert(CriticalAlert(**payload.model_dump()))
    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "ALERT_DELIVERY_FAILED",
                "message": "Failed to deliver critical alert",
                "details": result,
            },
        )

    return result
