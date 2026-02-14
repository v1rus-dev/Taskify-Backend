import base64
import binascii
import os
import secrets

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request


class AdminAuthBackend(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)
        self.admin_enabled = os.getenv("ENABLE_ADMIN", "false").lower() == "true"
        self.admin_user = os.getenv("ADMIN_BASIC_USER", "")
        self.admin_password = os.getenv("ADMIN_BASIC_PASSWORD", "")
        self.admin_token = os.getenv("ADMIN_TOKEN", "")

    @staticmethod
    def _decode_basic_header(encoded: str) -> tuple[str, str] | None:
        try:
            decoded = base64.b64decode(encoded).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return None

        username, separator, password = decoded.partition(":")
        if not separator:
            return None
        return username, password

    def _basic_is_valid(self, username: str, password: str) -> bool:
        if not self.admin_user or not self.admin_password:
            return False
        return secrets.compare_digest(username, self.admin_user) and secrets.compare_digest(
            password, self.admin_password
        )

    async def login(self, request: Request) -> bool:
        if not self.admin_enabled:
            return False

        form = await request.form()
        username = str(form.get("username", "")).strip()
        password = str(form.get("password", ""))
        if self._basic_is_valid(username, password):
            request.session["admin_actor"] = f"admin:{username}"
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        if not self.admin_enabled:
            return False

        session_actor = request.session.get("admin_actor")
        if session_actor:
            request.state.admin_actor = session_actor
            return True

        authorization = request.headers.get("authorization", "")
        if not authorization:
            return False

        scheme, _, credentials = authorization.partition(" ")
        scheme = scheme.lower()
        credentials = credentials.strip()
        if not credentials:
            return False

        if scheme == "bearer" and self.admin_token:
            if secrets.compare_digest(credentials, self.admin_token):
                request.state.admin_actor = "admin:token"
                request.session["admin_actor"] = "admin:token"
                return True

        if scheme == "basic":
            decoded = self._decode_basic_header(credentials)
            if not decoded:
                return False
            username, password = decoded
            if self._basic_is_valid(username, password):
                request.state.admin_actor = f"admin:{username}"
                request.session["admin_actor"] = f"admin:{username}"
                return True

        return False
