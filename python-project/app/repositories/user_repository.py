from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas import UserRead
from uuid import UUID


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_anonymous_user(self) -> User:
        """Создаёт нового анонимного пользователя."""
        new_user = User(is_anonymous=True)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Получает пользователя по ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def ensure_user_exists(self, user_id: UUID) -> None:
        """Проверяет существование пользователя. Выбрасывает HTTPException, если пользователь не найден."""
        user = self.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
