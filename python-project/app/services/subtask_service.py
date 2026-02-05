from typing import List, Optional
from app.errors import raise_http
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.task_repository import TaskRepository
from app.schemas import SubTaskRead, SubTaskCreate, SubTaskUpdate
from app.services.cache_service import CacheService
from app.services.sync_event_service import SyncEventService
from uuid import UUID


class SubTaskService:
    def __init__(
        self,
        subtask_repository: SubTaskRepository,
        task_repository: TaskRepository,
        cache_service: CacheService,
        sync_event_service: SyncEventService
    ):
        self.subtask_repository = subtask_repository
        self.task_repository = task_repository
        self.cache_service = cache_service
        self.sync_event_service = sync_event_service

    def _subtasks_cache_key(self, task_id: int) -> str:
        return f"subtasks:task:{task_id}"

    def create_subtasks(self, task_id: int, user_id: UUID, subtasks_data: List[dict]) -> List[SubTaskRead]:
        """Создаёт несколько подзадач."""
        # Проверяем, что задача существует и принадлежит пользователю
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise_http(404, "TASK_NOT_FOUND", "Task not found")
        
        created_subtasks = []
        for subtask_data in subtasks_data:
            subtask = self.subtask_repository.create(
                task_id,
                subtask_data["text"],
                subtask_data.get("is_completed", False)
            )
            created_subtasks.append(SubTaskRead.model_validate(subtask))
            self.sync_event_service.log_subtask_event(user_id, subtask.id, "create")
        self.cache_service.delete(self._subtasks_cache_key(task_id))
        return created_subtasks

    def get_subtasks(self, task_id: int, user_id: UUID, include_deleted: bool = False) -> List[SubTaskRead]:
        """Получает все подзадачи для задачи."""
        # Проверяем, что задача существует и принадлежит пользователю
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise_http(404, "TASK_NOT_FOUND", "Task not found")
        
        cache_key = self._subtasks_cache_key(task_id)
        if not include_deleted:
            cached = self.cache_service.get_json(cache_key)
            if cached is not None:
                return [SubTaskRead.model_validate(item) for item in cached]

        subtasks = self.subtask_repository.get_by_task_id(task_id, include_deleted=include_deleted)
        payload = [SubTaskRead.model_validate(subtask).model_dump() for subtask in subtasks]
        if not include_deleted:
            self.cache_service.set_json(cache_key, payload)
        return [SubTaskRead.model_validate(item) for item in payload]

    def update_subtasks(self, task_id: int, user_id: UUID, subtasks_data: List[dict]) -> List[SubTaskRead]:
        """Обновляет несколько подзадач."""
        # Проверяем, что задача существует и принадлежит пользователю
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise_http(404, "TASK_NOT_FOUND", "Task not found")
        
        updated_subtasks = []
        for subtask_data in subtasks_data:
            subtask_id = subtask_data["id"]
            subtask = self.subtask_repository.get_by_id_and_task_id(subtask_id, task_id)
            if not subtask:
                raise_http(404, "SUBTASK_NOT_FOUND", f"SubTask {subtask_id} not found")
            
            updated_subtask = self.subtask_repository.update(
                subtask,
                subtask_data.get("text"),
                subtask_data.get("is_completed")
            )
            updated_subtasks.append(SubTaskRead.model_validate(updated_subtask))
            self.sync_event_service.log_subtask_event(user_id, updated_subtask.id, "update")
        self.cache_service.delete(self._subtasks_cache_key(task_id))
        return updated_subtasks

    def delete_subtask(self, subtask_id: int, task_id: int, user_id: UUID) -> dict:
        """Удаляет подзадачу."""
        # Проверяем, что задача существует и принадлежит пользователю
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise_http(404, "TASK_NOT_FOUND", "Task not found")
        
        subtask = self.subtask_repository.get_by_id_and_task_id(subtask_id, task_id)
        if not subtask:
            raise_http(404, "SUBTASK_NOT_FOUND", "SubTask not found")
        
        deleted_subtask = self.subtask_repository.delete(subtask)
        self.sync_event_service.log_subtask_event(user_id, deleted_subtask.id, "delete")
        self.cache_service.delete(self._subtasks_cache_key(task_id))
        return {"message": "SubTask deleted successfully"}
