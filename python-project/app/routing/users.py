from fastapi import APIRouter, Depends
from app.depends import get_user_service
from app.services.user_service import UserService
from app.schemas import UserRead
from uuid import UUID
from app.routing.docs import error_response

router = APIRouter(prefix="/users", tags=["Users"])

@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user",
    description="Returns user profile by UUID.",
    responses={
        404: error_response("USER_NOT_FOUND", "User not found", "User not found."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid UUID format."),
    },
)
def get_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_user(user_id)
