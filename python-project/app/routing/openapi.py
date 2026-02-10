from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
import json

from app.depends import require_admin


router = APIRouter(prefix="/openapi", tags=["OpenAPI"])


@router.get("/yaml", response_class=PlainTextResponse)
def openapi_yaml(request: Request, _: None = Depends(require_admin)):
    return json.dumps(request.app.openapi(), ensure_ascii=False, indent=2)
