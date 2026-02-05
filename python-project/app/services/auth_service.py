import os
from typing import Optional, Dict, Any

import jwt
from jwt import PyJWKClient
from fastapi import status

from app.repositories.user_repository import UserRepository
from app.schemas import AuthResponse, UserRead, RefreshTokenResponse
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User
from app.errors import raise_http


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def authenticate_with_provider(self, provider: str, id_token: str) -> AuthResponse:
        claims = self._verify_id_token(id_token)
        provider_user_id = claims.get("sub")
        if not provider_user_id:
            raise_http(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Invalid token")

        email = claims.get("email")
        raw_name = claims.get("name") or claims.get("displayName")
        name = raw_name.strip() if raw_name else None
        avatar_url = (
            claims.get("picture")
            or claims.get("avatar_url")
            or claims.get("avatarUrl")
        )
        sign_in_provider = claims.get("firebase", {}).get("sign_in_provider", provider)

        user = self.user_repository.get_by_provider(sign_in_provider, provider_user_id)
        if not user:
            user = self.user_repository.create_oauth_user(
                provider=sign_in_provider,
                provider_user_id=provider_user_id,
                email=email,
                name=name,
                avatar_url=avatar_url
            )
        else:
            user = self.user_repository.update_profile(user, email, name, avatar_url)
        user = self.user_repository.ensure_friend_tag(user)

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user)
        )

    def refresh_token(self, refresh_token: str) -> RefreshTokenResponse:
        """Создаёт новый access токен используя refresh токен."""
        from app.core.security import decode_refresh_token
        
        try:
            payload = decode_refresh_token(refresh_token)
        except ValueError as exc:
            raise_http(
                status.HTTP_401_UNAUTHORIZED,
                "INVALID_REFRESH_TOKEN",
                "Invalid refresh token",
                details={"reason": str(exc)},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise_http(
                status.HTTP_401_UNAUTHORIZED,
                "TOKEN_MISSING_SUB",
                "Token missing subject (sub) claim",
            )
        
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise_http(status.HTTP_401_UNAUTHORIZED, "USER_NOT_FOUND", "User not found")
        
        # Создаём новую пару токенов
        new_access_token = create_access_token(str(user.id))
        new_refresh_token = create_refresh_token(str(user.id))
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )

    def link_password(self, user: User, email: str, password: str) -> AuthResponse:
        normalized_email = email.strip().lower()
        existing = self.user_repository.get_by_email(normalized_email)
        if existing and existing.id != user.id:
            raise_http(status.HTTP_409_CONFLICT, "EMAIL_ALREADY_IN_USE", "Email already in use")

        password_hash = hash_password(password)
        user = self.user_repository.set_email_and_password(user, normalized_email, password_hash)
        user = self.user_repository.ensure_friend_tag(user)
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user)
        )

    def login_with_password(self, email: str, password: str) -> AuthResponse:
        normalized_email = email.strip().lower()
        user = self.user_repository.get_by_email(normalized_email)
        if not user or not user.password_hash:
            raise_http(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise_http(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Invalid credentials")

        user = self.user_repository.ensure_friend_tag(user)
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user)
        )

    def _verify_id_token(self, id_token: str) -> Dict[str, Any]:
        jwks_url, issuer, audience = self._firebase_config()

        try:
            jwk_client = PyJWKClient(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(id_token)
            decoded = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=audience,
                issuer=issuer,
            )
            return decoded
        except jwt.ExpiredSignatureError as exc:
            raise_http(status.HTTP_401_UNAUTHORIZED, "TOKEN_EXPIRED", "Token expired")
        except jwt.InvalidAudienceError as exc:
            raise_http(
                status.HTTP_401_UNAUTHORIZED,
                "INVALID_TOKEN_AUDIENCE",
                "Invalid token audience",
                details={"expected": audience},
            )
        except jwt.InvalidIssuerError as exc:
            raise_http(
                status.HTTP_401_UNAUTHORIZED,
                "INVALID_TOKEN_ISSUER",
                "Invalid token issuer",
                details={"expected": issuer},
            )
        except jwt.PyJWTError as exc:
            print(f"JWT verification error: {type(exc).__name__}: {str(exc)}")
            raise_http(
                status.HTTP_401_UNAUTHORIZED,
                "INVALID_TOKEN",
                "Invalid token",
                details={"reason": str(exc)},
            )
        except Exception as exc:
            print(f"Unexpected error during token verification: {type(exc).__name__}: {str(exc)}")
            raise_http(
                status.HTTP_401_UNAUTHORIZED,
                "TOKEN_VERIFICATION_FAILED",
                "Token verification failed",
                details={"reason": str(exc)},
            )

    def _firebase_config(self) -> tuple[str, str, str]:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        if not project_id:
            raise_http(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "FIREBASE_CONFIG_MISSING",
                "Firebase configuration missing. Please set FIREBASE_PROJECT_ID environment variable in your .env file.",
            )

        jwks_url = os.getenv(
            "FIREBASE_JWKS_URL",
            "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"
        )
        issuer = os.getenv(
            "FIREBASE_ISSUER",
            f"https://securetoken.google.com/{project_id}"
        )

        return jwks_url, issuer, project_id
