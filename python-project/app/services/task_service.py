from typing import List, Optional
from fastapi import HTTPException
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas import TaskRead
from app.services.cache_service import CacheService
from uuid import UUID


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        user_repository: UserRepository,
        cache_service: CacheService
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.cache_service = cache_service

    def _tasks_cache_key(self, user_id: UUID) -> str:
        return f"tasks:user:{user_id}"

    def create_task(self, user_id: UUID, title: str, description: Optional[str]) -> TaskRead:
        """Создаёт новую задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.create(title, description, user_id)
        self.cache_service.delete(self._tasks_cache_key(user_id))
        return TaskRead.model_validate(task)

    def get_tasks(self, user_id: UUID) -> List[TaskRead]:
        """Получает все задачи пользователя."""
        self.user_repository.ensure_user_exists(user_id)
        cache_key = self._tasks_cache_key(user_id)
        cached = self.cache_service.get_json(cache_key)
        if cached is not None:
            return [TaskRead.model_validate(item) for item in cached]

        tasks = self.task_repository.get_by_user_id(user_id)
        payload = [TaskRead.model_validate(task).model_dump() for task in tasks]
        self.cache_service.set_json(cache_key, payload)
        return [TaskRead.model_validate(item) for item in payload]

    def update_task(self, task_id: int, user_id: UUID, title: Optional[str], description: Optional[str], is_completed: Optional[bool]) -> TaskRead:
        """Обновляет задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        updated_task = self.task_repository.update(task, title, description, is_completed)
        self.cache_service.delete(self._tasks_cache_key(user_id))
        return TaskRead.model_validate(updated_task)

    def delete_task(self, task_id: int, user_id: UUID) -> dict:
        """Удаляет задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        self.task_repository.delete(task)
        self.cache_service.delete(self._tasks_cache_key(user_id), f"subtasks:task:{task_id}")
        return {"message": "Task deleted successfully"}
