import asyncio
from typing import Any

from fastapi import HTTPException
from starlette.requests import Request

from app import main


class _StubAlertsClient:
    def __init__(self):
        self.sent_alerts = []

    async def send_critical_alert(self, alert) -> dict[str, Any]:
        self.sent_alerts.append(alert)
        return {"status": "sent"}


def _make_request(path: str = "/test", query: str = "") -> Request:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "query_string": query.encode("utf-8"),
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )
    request.state.request_id = "req-test-123"
    request.state.actor_id = "actor-test-456"
    return request


def test_http_exception_handler_sends_alert_for_5xx(monkeypatch):
    alerts_client = _StubAlertsClient()
    monkeypatch.setattr(main, "alerts_client", alerts_client)

    request = _make_request(path="/tasks", query="limit=50")
    exc = HTTPException(
        status_code=503,
        detail={
            "code": "UPSTREAM_UNAVAILABLE",
            "message": "Upstream timeout",
            "details": {"service": "db"},
        },
    )

    response = asyncio.run(main.http_exception_handler(request, exc))

    assert response.status_code == 503
    assert len(alerts_client.sent_alerts) == 1

    alert = alerts_client.sent_alerts[0]
    assert alert.title == "HTTP 503 error in API"
    assert alert.message == "Upstream timeout"
    assert alert.details["request_id"] == "req-test-123"
    assert alert.details["actor_id"] == "actor-test-456"
    assert alert.details["path"] == "/tasks"
    assert alert.details["query"] == "limit=50"
    assert alert.details["error_code"] == "UPSTREAM_UNAVAILABLE"


def test_http_exception_handler_does_not_send_alert_for_4xx(monkeypatch):
    alerts_client = _StubAlertsClient()
    monkeypatch.setattr(main, "alerts_client", alerts_client)

    request = _make_request(path="/tasks")
    exc = HTTPException(status_code=404, detail="Not found")

    response = asyncio.run(main.http_exception_handler(request, exc))

    assert response.status_code == 404
    assert alerts_client.sent_alerts == []


def test_http_exception_handler_does_not_loop_on_alert_delivery_failure(monkeypatch):
    alerts_client = _StubAlertsClient()
    monkeypatch.setattr(main, "alerts_client", alerts_client)

    request = _make_request(path="/internal/alerts/critical")
    exc = HTTPException(
        status_code=502,
        detail={
            "code": "ALERT_DELIVERY_FAILED",
            "message": "Failed to deliver critical alert",
            "details": {"status": "error"},
        },
    )

    response = asyncio.run(main.http_exception_handler(request, exc))

    assert response.status_code == 502
    assert alerts_client.sent_alerts == []


def test_unhandled_exception_handler_sends_alert(monkeypatch):
    alerts_client = _StubAlertsClient()
    monkeypatch.setattr(main, "alerts_client", alerts_client)

    request = _make_request(path="/sync/push")
    exc = RuntimeError("failed to process sync payload")

    response = asyncio.run(main.unhandled_exception_handler(request, exc))

    assert response.status_code == 500
    assert len(alerts_client.sent_alerts) == 1

    alert = alerts_client.sent_alerts[0]
    assert alert.title == "Unhandled exception in API"
    assert alert.message == "RuntimeError: failed to process sync payload"
    assert alert.details["status_code"] == 500
    assert alert.details["path"] == "/sync/push"
