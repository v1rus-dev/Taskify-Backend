from typing import List, Optional
from app.errors import raise_http
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.tag_repository import TagRepository
from app.schemas import TaskRead, TagInput
from app.services.cache_service import CacheService
from app.services.sync_event_service import SyncEventService
from uuid import UUID
from typing import Dict, Any


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        user_repository: UserRepository,
        tag_repository: TagRepository,
        cache_service: CacheService,
        sync_event_service: SyncEventService
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.tag_repository = tag_repository
        self.cache_service = cache_service
        self.sync_event_service = sync_event_service

    def _tasks_cache_key(self, user_id: UUID) -> str:
        return f"tasks:user:{user_id}"

    def _normalize_tag(self, tag: TagInput) -> Dict[str, Any]:
        if tag.is_user_tag:
            name = tag.name.strip() if tag.name else None
            color = tag.color.strip() if tag.color else None
        else:
            name = None
            color = None
        return {
            "id": tag.id,
            "is_user_tag": tag.is_user_tag,
            "name": name,
            "color": color,
        }

    def _resolve_tag(self, user_id: UUID, payload: Dict[str, Any]):
        if payload.get("id") is not None:
            existing = self.tag_repository.get_by_id(user_id, payload["id"])
            if existing:
                updated = self.tag_repository.update(
                    existing,
                    payload["is_user_tag"],
                    payload["name"],
                    payload["color"],
                )
                self.sync_event_service.log_tag_event(user_id, updated.id, "update")
                return updated

        existing = self.tag_repository.get_by_identity(
            user_id,
            payload["is_user_tag"],
            payload["name"],
            payload["color"],
        )
        if existing:
            return existing

        created = self.tag_repository.create(
            user_id,
            payload["is_user_tag"],
            payload["name"],
            payload["color"],
            payload.get("id"),
        )
        self.sync_event_service.log_tag_event(user_id, created.id, "create")
        return created

    def _sync_task_tags(self, task, user_id: UUID, tags: Optional[list[TagInput]]) -> bool:
        if tags is None:
            return False

        normalized = []
        seen_keys = set()
        for tag in tags:
            payload = self._normalize_tag(tag)
            key = (
                payload["id"]
                if payload["id"] is not None
                else (payload["is_user_tag"], payload["name"], payload["color"])
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            normalized.append(payload)

        resolved_tags = [self._resolve_tag(user_id, payload) for payload in normalized]
        target_ids = {tag.id for tag in resolved_tags}
        current_ids = {tag.id for tag in task.tags}

        changed = False
        for tag in resolved_tags:
            if tag.id not in current_ids:
                task.tags.append(tag)
                changed = True

        removed = [tag for tag in list(task.tags) if tag.id not in target_ids]
        if removed:
            for tag in removed:
                task.tags.remove(tag)
            changed = True

        if changed:
            self.tag_repository.commit()
            self.sync_event_service.log_task_event(user_id, task.id, "update")
            for tag in removed:
                if not self.tag_repository.is_tag_linked(user_id, tag.id):
                    self.tag_repository.delete(tag)
                    self.sync_event_service.log_tag_event(user_id, tag.id, "delete")

        return changed

    def create_task(self, user_id: UUID, title: str, description: Optional[str], tags: list[TagInput]) -> TaskRead:
        """Создаёт новую задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.create(title, description, user_id)
        tags_changed = self._sync_task_tags(task, user_id, tags)
        self.cache_service.delete(self._tasks_cache_key(user_id))
        self.sync_event_service.log_task_event(user_id, task.id, "create")
        if tags_changed:
            self.tag_repository.db.refresh(task)
        return TaskRead.model_validate(task)

    def get_tasks(self, user_id: UUID, include_deleted: bool = False) -> List[TaskRead]:
        """Получает все задачи пользователя."""
        self.user_repository.ensure_user_exists(user_id)
        cache_key = self._tasks_cache_key(user_id)
        if not include_deleted:
            cached = self.cache_service.get_json(cache_key)
            if cached is not None:
                return [TaskRead.model_validate(item) for item in cached]

        tasks = self.task_repository.get_by_user_id(user_id, include_deleted=include_deleted)
        payload = [TaskRead.model_validate(task).model_dump() for task in tasks]
        if not include_deleted:
            self.cache_service.set_json(cache_key, payload)
        return [TaskRead.model_validate(item) for item in payload]

    def update_task(self, task_id: int, user_id: UUID, title: Optional[str], description: Optional[str], is_completed: Optional[bool], tags: Optional[list[TagInput]]) -> TaskRead:
        """Обновляет задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise_http(404, "TASK_NOT_FOUND", "Task not found")
        
        updated_task = self.task_repository.update(task, title, description, is_completed)
        tags_changed = self._sync_task_tags(updated_task, user_id, tags)
        self.cache_service.delete(self._tasks_cache_key(user_id))
        self.sync_event_service.log_task_event(user_id, updated_task.id, "update")
        if tags_changed:
            self.tag_repository.db.refresh(updated_task)
        return TaskRead.model_validate(updated_task)

    def delete_task(self, task_id: int, user_id: UUID) -> dict:
        """Удаляет задачу."""
        self.user_repository.ensure_user_exists(user_id)
        
        task = self.task_repository.get_by_id_and_user_id(task_id, user_id)
        if not task:
            raise_http(404, "TASK_NOT_FOUND", "Task not found")
        
        deleted_task = self.task_repository.delete(task)
        self.cache_service.delete(self._tasks_cache_key(user_id), f"subtasks:task:{task_id}")
        self.sync_event_service.log_task_event(user_id, deleted_task.id, "delete")
        return TaskRead.model_validate(deleted_task)
