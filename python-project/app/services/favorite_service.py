from typing import List
from fastapi import HTTPException
from app.repositories.user_repository import UserRepository
from app.schemas import TaskRead
from uuid import UUID


class FavoriteService:
    def __init__(
        self,
        user_repository: UserRepository
    ):
        self.user_repository = user_repository

    def add_favorite_task(self, task_id: int, user_id: UUID) -> dict:
        """Добавляет задачу в избранное."""
        self.user_repository.ensure_user_exists(user_id)
        
        raise NotImplementedError("FavoriteTaskRepository was removed")

    def get_favorite_tasks(self, user_id: UUID) -> List[TaskRead]:
        """Получает все избранные задачи пользователя."""
        self.user_repository.ensure_user_exists(user_id)
        
        raise NotImplementedError("FavoriteTaskRepository was removed")
