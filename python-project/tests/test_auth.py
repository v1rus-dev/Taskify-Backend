from types import SimpleNamespace
from datetime import datetime, timezone
from uuid import uuid4

from app.depends import get_auth_service, get_current_user
from app.schemas import AuthResponse, UserRead
from app.errors import raise_http
from app.schemas.auth_schemas import RefreshTokenResponse


class FakeAuthService:
    def __init__(self, user):
        self.user = user

    def authenticate_with_provider(self, provider: str, id_token: str) -> AuthResponse:
        return AuthResponse(
            access_token="access",
            refresh_token="refresh",
            user=UserRead(
                id=self.user.id,
                provider="test",
                provider_user_id="provider-id",
                email=self.user.email,
                name=self.user.name,
                avatar_url=self.user.avatar_url,
                friend_tag=self.user.friend_tag,
                created_at=self.user.created_at,
                updated_at=self.user.updated_at,
            ),
        )

    def link_password(self, user, email: str, password: str) -> AuthResponse:
        return AuthResponse(
            access_token="access",
            refresh_token="refresh",
            user=UserRead(
                id=user.id,
                provider="test",
                provider_user_id="provider-id",
                email=user.email,
                name=user.name,
                avatar_url=user.avatar_url,
                friend_tag=user.friend_tag,
                created_at=user.created_at,
                updated_at=user.updated_at,
            ),
        )

    def login_with_password(self, email: str, password: str) -> AuthResponse:
        raise_http(401, "INVALID_CREDENTIALS", "Invalid credentials")

    def refresh_token(self, refresh_token: str) -> RefreshTokenResponse:
        return RefreshTokenResponse(access_token="access2", refresh_token="refresh2")


def _user(name: str, email: str):
    return SimpleNamespace(
        id=uuid4(),
        email=email,
        name=name,
        avatar_url=None,
        friend_tag="TEST-TAG",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


def test_auth_with_provider_success(client):
    user = _user("Alice", "alice@example.com")
    app_overrides = client.app.dependency_overrides
    app_overrides[get_auth_service] = lambda: FakeAuthService(user)

    response = client.post("/auth", json={"provider": "firebase", "id_token": "token"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "access"
    assert payload["refresh_token"] == "refresh"
    assert payload["token_type"] == "bearer"
    assert payload["user"]["id"] == str(user.id)


def test_login_with_password_invalid_credentials(client):
    user = _user("Bob", "bob@example.com")
    app_overrides = client.app.dependency_overrides
    app_overrides[get_auth_service] = lambda: FakeAuthService(user)

    response = client.post("/auth/password/login", json={"email": "bob@example.com", "password": "badpassword"})
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "INVALID_CREDENTIALS"
    assert payload["error"]["message"] == "Invalid credentials"


def test_link_password_success(client):
    user = _user("Eve", "eve@example.com")
    app_overrides = client.app.dependency_overrides
    app_overrides[get_auth_service] = lambda: FakeAuthService(user)
    app_overrides[get_current_user] = lambda: user

    response = client.post("/auth/password/link", json={"email": "new@example.com", "password": "longpassword"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["id"] == str(user.id)
