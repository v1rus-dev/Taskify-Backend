from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import INTERNAL_ALERTS_API_KEY
from app.services.telegram_alerts import CriticalAlert, TelegramAlertsClient

app = FastAPI(title="Tasky - Mini Todo API")
alerts_client = TelegramAlertsClient()


class CriticalAlertRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=4000)
    source: str = Field(default="taskify-backend", min_length=1, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=10)
    details: dict[str, Any] | None = None

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Проверка статуса сервиса.
    Возвращает JSON с информацией о работе API.
    """
    return {"status": "ok", "service": "Tasky Backend"}


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await alerts_client.close()


@app.post("/internal/alerts/critical", tags=["Internal"])
async def send_critical_alert(
    payload: CriticalAlertRequest,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    if INTERNAL_ALERTS_API_KEY and x_internal_key != INTERNAL_ALERTS_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal key")

    result = await alerts_client.send_critical_alert(CriticalAlert(**payload.model_dump()))
    if result.get("status") == "error":
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result)

    return result
