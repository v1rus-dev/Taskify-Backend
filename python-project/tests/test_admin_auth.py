import asyncio
import base64

from starlette.requests import Request

from admin_app.auth import AdminAuthBackend


def _request_with_headers(headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/admin",
            "headers": headers,
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
            "session": {},
        }
    )


def test_authenticate_with_basic_header(monkeypatch):
    monkeypatch.setenv("ENABLE_ADMIN", "true")
    monkeypatch.setenv("ADMIN_BASIC_USER", "admin")
    monkeypatch.setenv("ADMIN_BASIC_PASSWORD", "adminpass")
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    backend = AdminAuthBackend(secret_key="test-secret")

    encoded = base64.b64encode(b"admin:adminpass").decode("utf-8")
    request = _request_with_headers([(b"authorization", f"Basic {encoded}".encode("utf-8"))])

    is_authenticated = asyncio.run(backend.authenticate(request))

    assert is_authenticated is True
    assert request.state.admin_actor == "admin:admin"
    assert request.session["admin_actor"] == "admin:admin"


def test_authenticate_with_bearer_admin_token(monkeypatch):
    monkeypatch.setenv("ENABLE_ADMIN", "true")
    monkeypatch.setenv("ADMIN_TOKEN", "token-123")
    monkeypatch.delenv("ADMIN_BASIC_USER", raising=False)
    monkeypatch.delenv("ADMIN_BASIC_PASSWORD", raising=False)
    backend = AdminAuthBackend(secret_key="test-secret")

    request = _request_with_headers([(b"authorization", b"Bearer token-123")])
    is_authenticated = asyncio.run(backend.authenticate(request))

    assert is_authenticated is True
    assert request.state.admin_actor == "admin:token"
    assert request.session["admin_actor"] == "admin:token"


def test_authenticate_invalid_credentials(monkeypatch):
    monkeypatch.setenv("ENABLE_ADMIN", "true")
    monkeypatch.setenv("ADMIN_BASIC_USER", "admin")
    monkeypatch.setenv("ADMIN_BASIC_PASSWORD", "adminpass")
    monkeypatch.setenv("ADMIN_TOKEN", "token-123")
    backend = AdminAuthBackend(secret_key="test-secret")

    request = _request_with_headers([(b"authorization", b"Bearer bad-token")])
    is_authenticated = asyncio.run(backend.authenticate(request))

    assert is_authenticated is False
