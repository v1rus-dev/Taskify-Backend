from fastapi import APIRouter, Depends
from typing import List

from app.depends import get_tag_service, get_current_user
from app.services.tag_service import TagService
from app.schemas import TagRead
from app.models.user import User
from app.routing.docs import error_response


router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get(
    "/user",
    response_model=List[TagRead],
    summary="List user tags",
    description="Returns tags for the current user.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
    },
)
def get_user_tags(
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
):
    return tag_service.get_user_tags(current_user.id, include_deleted=include_deleted)
