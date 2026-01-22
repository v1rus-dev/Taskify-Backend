from fastapi import HTTPException
from app.repositories.user_repository import UserRepository
from app.schemas import UserRead
from uuid import UUID


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_user(self, user_id: UUID) -> UserRead:
        """Получает пользователя по ID."""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserRead(
            id=user.id,
            provider=user.provider,
            provider_user_id=user.provider_user_id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            friend_tag=user.friend_tag,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
