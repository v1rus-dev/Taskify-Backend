from typing import List
from fastapi import HTTPException
from app.repositories.favorite_task_repository import FavoriteTaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas import TaskRead
from uuid import UUID


class FavoriteService:
    def __init__(
        self,
        favorite_task_repository: FavoriteTaskRepository,
        user_repository: UserRepository
    ):
        self.favorite_task_repository = favorite_task_repository
        self.user_repository = user_repository

    def add_favorite_task(self, task_id: int, user_id: UUID) -> dict:
        """Добавляет задачу в избранное."""
        self.user_repository.ensure_user_exists(user_id)
        
        self.favorite_task_repository.create(task_id, user_id)
        return {"message": "Task added to favorites"}

    def get_favorite_tasks(self, user_id: UUID) -> List[TaskRead]:
        """Получает все избранные задачи пользователя."""
        self.user_repository.ensure_user_exists(user_id)
        
        tasks = self.favorite_task_repository.get_favorite_tasks_by_user_id(user_id)
        
        # Обогащаем задачи информацией об избранном (все будут is_favorite=True)
        favorite_task_ids = self.favorite_task_repository.get_favorite_task_ids_by_user_id_and_task_ids(
            user_id, [task.id for task in tasks]
        )
        
        result = []
        for task in tasks:
            result.append(TaskRead(
                id=task.id,
                title=task.title,
                description=task.description,
                is_completed=task.is_completed,
                user_id=task.user_id,
                is_favorite=task.id in favorite_task_ids,
                created_at=task.created_at,
                updated_at=task.updated_at
            ))
        return result
