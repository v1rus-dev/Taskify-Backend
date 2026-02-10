"""Deprecated admin router.

This project moved to SQLAdmin in `admin_app.main`. Legacy endpoints are intentionally
not available anymore.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/admin-legacy", tags=["Admin (deprecated)"])


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def legacy_admin_not_available(path: str):
    raise HTTPException(
        status_code=410,
        detail={
            "code": "ADMIN_LEGACY_REMOVED",
            "message": "Legacy admin endpoints were removed. Use SQLAdmin at /admin.",
            "path": path,
        },
    )
