from typing import List, Optional
from fastapi import HTTPException
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.task_repository import TaskRepository
from app.schemas import SubTaskRead, SubTaskCreate, SubTaskUpdate
from uuid import UUID


class SubTaskService:
    def __init__(
        self,
        subtask_repository: SubTaskRepository,
        task_repository: TaskRepository
    ):
        self.subtask_repository = subtask_repository
        self.task_repository = task_repository

    def create_subtasks(self, task_id: int, user_id: UUID, subtasks_data: List[dict]) -> List[SubTaskRead]:
        """Создаёт несколько подзадач."""
        # Проверяем, что задача существует и принадлежит пользователю
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        created_subtasks = []
        for subtask_data in subtasks_data:
            subtask = self.subtask_repository.create(
                task_id,
                subtask_data["text"],
                subtask_data.get("is_completed", False)
            )
            created_subtasks.append(SubTaskRead.model_validate(subtask))
        
        return created_subtasks

    def get_subtasks(self, task_id: int, user_id: UUID) -> List[SubTaskRead]:
        """Получает все подзадачи для задачи."""
        # Проверяем, что задача существует и принадлежит пользователю
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        subtasks = self.subtask_repository.get_by_task_id(task_id)
        return [SubTaskRead.model_validate(subtask) for subtask in subtasks]

    def update_subtasks(self, task_id: int, user_id: UUID, subtasks_data: List[dict]) -> List[SubTaskRead]:
        """Обновляет несколько подзадач."""
        # Проверяем, что задача существует и принадлежит пользователю
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        updated_subtasks = []
        for subtask_data in subtasks_data:
            subtask_id = subtask_data["id"]
            subtask = self.subtask_repository.get_by_id_and_task_id(subtask_id, task_id)
            if not subtask:
                raise HTTPException(status_code=404, detail=f"SubTask {subtask_id} not found")
            
            updated_subtask = self.subtask_repository.update(
                subtask,
                subtask_data.get("text"),
                subtask_data.get("is_completed")
            )
            updated_subtasks.append(SubTaskRead.model_validate(updated_subtask))
        
        return updated_subtasks

    def delete_subtask(self, subtask_id: int, task_id: int, user_id: UUID) -> dict:
        """Удаляет подзадачу."""
        # Проверяем, что задача существует и принадлежит пользователю
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        subtask = self.subtask_repository.get_by_id_and_task_id(subtask_id, task_id)
        if not subtask:
            raise HTTPException(status_code=404, detail="SubTask not found")
        
        self.subtask_repository.delete(subtask)
        return {"message": "SubTask deleted successfully"}
