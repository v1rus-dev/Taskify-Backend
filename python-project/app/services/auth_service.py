import os
from typing import Optional, Dict, Any

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.schemas import AuthResponse, UserRead
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def authenticate_with_provider(self, provider: str, id_token: str) -> AuthResponse:
        print(f"Authenticating with provider: {provider} and id_token: {id_token}")
        claims = self._verify_id_token(id_token)
        provider_user_id = claims.get("sub")
        if not provider_user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        email = claims.get("email")
        sign_in_provider = claims.get("firebase", {}).get("sign_in_provider", provider)

        user = self.user_repository.get_by_provider(sign_in_provider, provider_user_id)
        if not user:
            # Новый пользователь - создаем с пустыми name и avatar_url
            user = self.user_repository.create_oauth_user(
                provider=sign_in_provider,
                provider_user_id=provider_user_id,
                email=email,
                name=None,
                avatar_url=None
            )
        else:
            # Существующий пользователь - обновляем только email, name и avatar_url берем из БД
            user = self.user_repository.update_profile(user, email, None, None)

        access_token = create_access_token(str(user.id))
        return AuthResponse(access_token=access_token, user=UserRead.model_validate(user))

    def link_password(self, user: User, email: str, password: str) -> AuthResponse:
        normalized_email = email.strip().lower()
        existing = self.user_repository.get_by_email(normalized_email)
        if existing and existing.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

        password_hash = hash_password(password)
        user = self.user_repository.set_email_and_password(user, normalized_email, password_hash)
        access_token = create_access_token(str(user.id))
        return AuthResponse(access_token=access_token, user=UserRead.model_validate(user))

    def login_with_password(self, email: str, password: str) -> AuthResponse:
        normalized_email = email.strip().lower()
        user = self.user_repository.get_by_email(normalized_email)
        if not user or not user.password_hash:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = create_access_token(str(user.id))
        return AuthResponse(access_token=access_token, user=UserRead.model_validate(user))

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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
        except jwt.InvalidAudienceError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token audience. Expected: {audience}") from exc
        except jwt.InvalidIssuerError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token issuer. Expected: {issuer}") from exc
        except jwt.PyJWTError as exc:
            print(f"JWT verification error: {type(exc).__name__}: {str(exc)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(exc)}") from exc
        except Exception as exc:
            print(f"Unexpected error during token verification: {type(exc).__name__}: {str(exc)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token verification failed: {str(exc)}") from exc

    def _firebase_config(self) -> tuple[str, str, str]:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Firebase configuration missing. Please set FIREBASE_PROJECT_ID environment variable in your .env file."
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
