from typing import List, Optional
from fastapi import HTTPException
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.favorite_task_repository import FavoriteTaskRepository
from app.schemas import TaskRead
from uuid import UUID


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        user_repository: UserRepository,
        favorite_task_repository: FavoriteTaskRepository
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.favorite_task_repository = favorite_task_repository

    def _enrich_task_with_favorite(self, task, user_id: UUID) -> TaskRead:
        """Обогащает задачу информацией об избранном."""
        favorite_task_ids = self.favorite_task_repository.get_favorite_task_ids_by_user_id_and_task_ids(
            user_id, [task.id]
        )
        return TaskRead(
            id=task.id,
            title=task.title,
            description=task.description,
            is_completed=task.is_completed,
            user_id=task.user_id,
            is_favorite=task.id in favorite_task_ids,
            created_at=task.created_at,
            updated_at=task.updated_at
        )

    def _enrich_tasks_with_favorite(self, tasks: List, user_id: UUID) -> List[TaskRead]:
        """Обогащает список задач информацией об избранном."""
        if not tasks:
            return []
        
        task_ids = [task.id for task in tasks]
        favorite_task_ids = self.favorite_task_repository.get_favorite_task_ids_by_user_id_and_task_ids(
            user_id, task_ids
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

    def create_task(self, user_id: UUID, title: str, description: Optional[str]) -> TaskRead:
        """Создаёт новую задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.create(title, description, user_id)
        return self._enrich_task_with_favorite(task, user_id)

    def get_tasks(self, user_id: UUID) -> List[TaskRead]:
        """Получает все задачи пользователя."""
        self.user_repository.ensure_user_exists(user_id)
        
        tasks = self.task_repository.get_by_user_id(user_id)
        return self._enrich_tasks_with_favorite(tasks, user_id)

    def update_task(self, task_id: int, user_id: UUID, title: str, description: Optional[str], is_completed: Optional[bool]) -> TaskRead:
        """Обновляет задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        updated_task = self.task_repository.update(task, title, description, is_completed)
        return self._enrich_task_with_favorite(updated_task, user_id)

    def delete_task(self, task_id: int, user_id: UUID) -> dict:
        """Удаляет задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        self.task_repository.delete(task)
        return {"message": "Task deleted successfully"}
