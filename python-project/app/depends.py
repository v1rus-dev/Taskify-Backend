"""
Файл внедрения зависимостей
"""
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.subtask_repository import SubTaskRepository
from app.services.user_service import UserService
from app.services.task_service import TaskService
from app.services.auth_service import AuthService
from app.services.subtask_service import SubTaskService
from app.core.security import decode_access_token
from uuid import UUID


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Создаёт репозиторий пользователей."""
    return UserRepository(db)


def get_task_repository(db: Session = Depends(get_db)) -> TaskRepository:
    """Создаёт репозиторий задач."""
    return TaskRepository(db)


def get_subtask_repository(db: Session = Depends(get_db)) -> SubTaskRepository:
    """Создаёт репозиторий подзадач."""
    return SubTaskRepository(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Создаёт сервис пользователей."""
    user_repository = UserRepository(db)
    return UserService(user_repository)


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """Создаёт сервис задач."""
    task_repository = TaskRepository(db)
    user_repository = UserRepository(db)
    return TaskService(task_repository, user_repository)




def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Создаёт сервис аутентификации."""
    user_repository = UserRepository(db)
    return AuthService(user_repository)


def get_subtask_service(db: Session = Depends(get_db)) -> SubTaskService:
    """Создаёт сервис подзадач."""
    subtask_repository = SubTaskRepository(db)
    task_repository = TaskRepository(db)
    return SubTaskService(subtask_repository, task_repository)


auth_scheme = HTTPBearer()
admin_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    user_repository: UserRepository = Depends(get_user_repository)
):
    """Аутентификация через JWT."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid"
        )
    
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(exc)}"
        ) from exc

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject (sub) claim"
        )

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user ID format in token: {str(exc)}"
        ) from exc

    user = user_repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not found: {user_id}"
        )
    return user


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(admin_scheme),
) -> None:
    if os.getenv("ENABLE_ADMIN", "false").lower() != "true":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access is disabled"
        )

    admin_token = os.getenv("ADMIN_TOKEN")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access is disabled"
        )

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid"
        )

    if credentials.credentials != admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token"
        )
