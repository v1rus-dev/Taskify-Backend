from typing import Any, Optional
from fastapi import HTTPException


def error_detail(code: str, message: str, details: Optional[Any] = None) -> dict:
    payload = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return payload


def raise_http(status_code: int, code: str, message: str, details: Optional[Any] = None) -> None:
    raise HTTPException(status_code=status_code, detail=error_detail(code, message, details))
