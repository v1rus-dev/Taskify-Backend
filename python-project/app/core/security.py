import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be set")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 дней
JWT_REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", "43200"))  # 30 дней

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    """Создаёт access токен (живёт месяц по умолчанию)."""
    expire_minutes = expires_minutes if expires_minutes is not None else JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    """Создаёт refresh токен (живёт неделю по умолчанию)."""
    expire_minutes = expires_minutes if expires_minutes is not None else JWT_REFRESH_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Декодирует access токен."""
    if not token:
        raise ValueError("Token is empty")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        token_type = payload.get("type")
        if token_type != "access":
            raise ValueError("Invalid token type: expected access token")
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token expired") from exc
    except jwt.DecodeError as exc:
        raise ValueError(f"Token decode error: {str(exc)}") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid token: {str(exc)}") from exc
    except Exception as exc:
        raise ValueError(f"Token validation error: {str(exc)}") from exc


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """Декодирует refresh токен."""
    if not token:
        raise ValueError("Token is empty")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        token_type = payload.get("type")
        if token_type != "refresh":
            raise ValueError("Invalid token type: expected refresh token")
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token expired") from exc
    except jwt.DecodeError as exc:
        raise ValueError(f"Token decode error: {str(exc)}") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid token: {str(exc)}") from exc
    except Exception as exc:
        raise ValueError(f"Token validation error: {str(exc)}") from exc


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)
