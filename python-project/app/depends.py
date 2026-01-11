"""
Файл внедрения зависимостей
"""
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.task_repository import TaskRepository
from app.services.user_service import UserService
from app.services.task_service import TaskService
from app.services.favorite_service import FavoriteService


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Создаёт репозиторий пользователей."""
    return UserRepository(db)


def get_task_repository(db: Session = Depends(get_db)) -> TaskRepository:
    """Создаёт репозиторий задач."""
    return TaskRepository(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Создаёт сервис пользователей."""
    user_repository = UserRepository(db)
    return UserService(user_repository)


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """Создаёт сервис задач."""
    task_repository = TaskRepository(db)
    user_repository = UserRepository(db)
    return TaskService(task_repository, user_repository)


def get_favorite_service(db: Session = Depends(get_db)) -> FavoriteService:
    """Создаёт сервис избранных задач."""
    user_repository = UserRepository(db)
    return FavoriteService(user_repository)
