import html
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.bot_runtime import BotRuntime
from app.config import Settings

app = FastAPI(title="Taskify Telegram Bot Gateway")
bot_runtime = BotRuntime()


class NotifyRequest(BaseModel):
    severity: Literal["critical", "warning", "info"] = "critical"
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=4000)
    source: str = Field(default="taskify-backend", min_length=1, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=10)
    details: dict[str, Any] | None = None


def _alert_emoji(severity: str) -> str:
    if severity == "critical":
        return "🚨"
    if severity == "warning":
        return "⚠️"
    return "ℹ️"


def _format_alert_message(payload: NotifyRequest) -> str:
    parts = [
        f"{_alert_emoji(payload.severity)} <b>{html.escape(payload.title)}</b>",
        f"<b>Уровень:</b> {html.escape(payload.severity.upper())}",
        f"<b>Источник:</b> {html.escape(payload.source)}",
        "",
        html.escape(payload.message),
    ]

    if payload.tags:
        safe_tags = ", ".join(html.escape(tag) for tag in payload.tags)
        parts.extend(["", f"<b>Теги:</b> {safe_tags}"])

    if payload.details:
        parts.append("")
        parts.append("<b>Детали:</b>")
        for key, value in payload.details.items():
            parts.append(f"• <b>{html.escape(str(key))}:</b> <code>{html.escape(str(value))}</code>")

    return "\n".join(parts)


async def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-Api-Key")) -> None:
    if not Settings.api_key:
        return
    if x_api_key == Settings.api_key:
        return
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@app.on_event("startup")
async def on_startup() -> None:
    await bot_runtime.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await bot_runtime.stop()


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    bot_status = "running" if bot_runtime.is_ready else "disabled"
    return {"status": "ok", "bot": bot_status}


@app.post("/api/v1/notify", dependencies=[Depends(verify_api_key)], tags=["Notifications"])
async def notify(payload: NotifyRequest) -> dict[str, Any]:
    if not bot_runtime.is_ready:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram bot is disabled")

    try:
        delivered_to = await bot_runtime.broadcast_html(_format_alert_message(payload))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return {"status": "sent", "delivered_to": delivered_to}
