from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import (
    TELEGRAM_ALERTS_ENABLED,
    TELEGRAM_BOT_GATEWAY_API_KEY,
    TELEGRAM_BOT_GATEWAY_URL,
    TELEGRAM_REQUEST_TIMEOUT_SECONDS,
)


class CriticalAlert(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=4000)
    source: str = Field(default="taskify-backend", min_length=1, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=10)
    details: dict[str, Any] | None = None


class TelegramAlertsClient:
    def __init__(self) -> None:
        self._http_client = httpx.AsyncClient(timeout=TELEGRAM_REQUEST_TIMEOUT_SECONDS)

    async def close(self) -> None:
        await self._http_client.aclose()

    async def send_critical_alert(self, alert: CriticalAlert) -> dict[str, Any]:
        if not TELEGRAM_ALERTS_ENABLED:
            return {"status": "disabled"}

        headers = {"X-Api-Key": TELEGRAM_BOT_GATEWAY_API_KEY} if TELEGRAM_BOT_GATEWAY_API_KEY else {}
        payload = {
            "severity": "critical",
            "title": alert.title,
            "message": alert.message,
            "source": alert.source,
            "tags": alert.tags,
            "details": alert.details,
        }

        try:
            response = await self._http_client.post(TELEGRAM_BOT_GATEWAY_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            return {"status": "error", "reason": str(exc)}
