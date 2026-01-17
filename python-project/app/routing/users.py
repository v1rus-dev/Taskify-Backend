from fastapi import APIRouter, Depends
from app.depends import get_user_service
from app.services.user_service import UserService
from app.schemas import UserRead
from uuid import UUID

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    """
    Получает пользователя по UUID.
    """
    return user_service.get_user(user_id)
