from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from uuid import UUID


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Получает пользователя по ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_provider(self, provider: str, provider_user_id: str) -> Optional[User]:
        """Получает пользователя по провайдеру и его идентификатору."""
        return (
            self.db.query(User)
            .filter(User.provider == provider, User.provider_user_id == provider_user_id)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """Получает пользователя по email."""
        return self.db.query(User).filter(User.email == email).first()

    def create_oauth_user(
        self,
        provider: str,
        provider_user_id: str,
        email: Optional[str],
        name: Optional[str],
        avatar_url: Optional[str]
    ) -> User:
        """Создаёт нового пользователя из OAuth провайдера."""
        new_user = User(
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            name=name,
            avatar_url=avatar_url
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def update_profile(
        self,
        user: User,
        email: Optional[str],
        name: Optional[str],
        avatar_url: Optional[str]
    ) -> User:
        """Обновляет профиль пользователя, если есть новые данные."""
        updated = False
        if email and user.email != email:
            user.email = email
            updated = True
        if name and user.name != name:
            user.name = name
            updated = True
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            updated = True
        if updated:
            self.db.commit()
            self.db.refresh(user)
        return user

    def set_email_and_password(self, user: User, email: str, password_hash: str) -> User:
        """Привязывает email и пароль к пользователю."""
        user.email = email
        user.password_hash = password_hash
        self.db.commit()
        self.db.refresh(user)
        return user

    def ensure_user_exists(self, user_id: UUID) -> None:
        """Проверяет существование пользователя. Выбрасывает HTTPException, если пользователь не найден."""
        user = self.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
