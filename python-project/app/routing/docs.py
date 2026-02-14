from typing import Any, Optional
from app.schemas import ErrorResponse


def error_example(code: str, message: str, details: Optional[Any] = None) -> dict:
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return payload


def error_response(code: str, message: str, description: str, details: Optional[Any] = None) -> dict:
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {
            "application/json": {
                "example": error_example(code, message, details),
            }
        },
    }
