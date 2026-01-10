from fastapi import HTTPException
from app.repositories.user_repository import UserRepository
from app.schemas import UserRead
from uuid import UUID


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_anonymous_user(self) -> UserRead:
        """Создаёт нового анонимного пользователя."""
        user = self.repository.create_anonymous_user()
        return UserRead(
            id=user.id,
            is_anonymous=user.is_anonymous,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    def get_user(self, user_id: UUID) -> UserRead:
        """Получает пользователя по ID."""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserRead(
            id=user.id,
            is_anonymous=user.is_anonymous,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
