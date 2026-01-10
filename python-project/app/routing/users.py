from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.depends import get_user_service
from app.services.user_service import UserService
from app.schemas import UserRead
from uuid import UUID

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/create/anonymous", response_model=UserRead)
def create_anonymous_user(
    user_service: UserService = Depends(get_user_service)
):
    """
    Создаёт нового анонимного пользователя и возвращает его user_id (UUID).
    """
    return user_service.create_anonymous_user()

@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    """
    Получает пользователя по UUID.
    """
    return user_service.get_user(user_id)
