import logging
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core.logging import extract_actor_id, register_request_logging
from app.core.security import create_access_token


class _CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def test_extract_actor_id_from_valid_bearer_token():
    user_id = str(uuid4())
    token = create_access_token(user_id)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/ping",
            "headers": [(b"authorization", f"Bearer {token}".encode("utf-8"))],
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )

    actor_id = extract_actor_id(request)
    assert actor_id == user_id


def test_extract_actor_id_invalid_token_returns_anonymous():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/ping",
            "headers": [(b"authorization", b"Bearer invalid-token")],
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )

    actor_id = extract_actor_id(request)
    assert actor_id == "anonymous"


def test_request_logging_middleware_writes_expected_fields():
    logger_name = "tests.request_logger"
    logger = logging.getLogger(logger_name)
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False

    capture_handler = _CaptureHandler()
    logger.addHandler(capture_handler)

    user_id = str(uuid4())
    token = create_access_token(user_id)

    app = FastAPI()
    register_request_logging(app, service_name="test-service", logger_name=logger_name)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    response = client.get(
        "/ping",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Request-ID": "req-123",
            "X-Forwarded-For": "203.0.113.10",
            "User-Agent": "pytest-client",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"
    assert capture_handler.records, "No request log record captured"

    record = capture_handler.records[-1]
    assert record.service == "test-service"
    assert record.request_id == "req-123"
    assert record.actor_id == user_id
    assert record.method == "GET"
    assert record.path == "/ping"
    assert record.status_code == 200
    assert isinstance(record.duration_ms, float)
    assert record.client_ip == "203.0.113.10"
    assert record.user_agent == "pytest-client"
