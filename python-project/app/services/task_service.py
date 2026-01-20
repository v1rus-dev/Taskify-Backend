from typing import List, Optional
from fastapi import HTTPException
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas import TaskRead
from uuid import UUID


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        user_repository: UserRepository
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository

    def create_task(self, user_id: UUID, title: str, description: Optional[str]) -> TaskRead:
        """Создаёт новую задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.create(title, description, user_id)
        return TaskRead.model_validate(task)

    def get_tasks(self, user_id: UUID) -> List[TaskRead]:
        """Получает все задачи пользователя."""
        self.user_repository.ensure_user_exists(user_id)
        
        tasks = self.task_repository.get_by_user_id(user_id)
        return [TaskRead.model_validate(task) for task in tasks]

    def update_task(self, task_id: int, user_id: UUID, title: Optional[str], description: Optional[str], is_completed: Optional[bool]) -> TaskRead:
        """Обновляет задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        updated_task = self.task_repository.update(task, title, description, is_completed)
        return TaskRead.model_validate(updated_task)

    def delete_task(self, task_id: int, user_id: UUID) -> dict:
        """Удаляет задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        self.task_repository.delete(task)
        return {"message": "Task deleted successfully"}
