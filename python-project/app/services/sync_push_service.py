from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from app.repositories.task_repository import TaskRepository
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.user_repository import UserRepository
from app.repositories.sync_op_repository import SyncOpRepository
from app.services.sync_event_service import SyncEventService
from app.schemas import SyncOpInput, SyncOpError, SyncIdMap, SyncOpData


class SyncPushService:
    allowed_entities = {"task", "subtask", "tag"}
    allowed_ops = {"create", "update", "delete"}

    def __init__(
        self,
        task_repository: TaskRepository,
        subtask_repository: SubTaskRepository,
        tag_repository: TagRepository,
        user_repository: UserRepository,
        sync_op_repository: SyncOpRepository,
        sync_event_service: SyncEventService,
    ):
        self.task_repository = task_repository
        self.subtask_repository = subtask_repository
        self.tag_repository = tag_repository
        self.user_repository = user_repository
        self.sync_op_repository = sync_op_repository
        self.sync_event_service = sync_event_service

    def process(self, user_id: UUID, device_id: Optional[str], ops: List[SyncOpInput]):
        self.user_repository.ensure_user_exists(user_id)
        id_map: Dict[str, List[SyncIdMap]] = {"task": [], "subtask": [], "tag": []}
        ack: List[UUID] = []
        errors: List[SyncOpError] = []

        for op in ops:
            if self.sync_op_repository.exists(user_id, op.op_id):
                ack.append(op.op_id)
                continue

            try:
                self._apply_op(user_id, op, id_map)
                self.sync_op_repository.create(user_id, op.op_id, device_id)
                ack.append(op.op_id)
            except ValueError as exc:
                errors.append(SyncOpError(op_id=op.op_id, code="invalid", message=str(exc)))
            except LookupError as exc:
                errors.append(SyncOpError(op_id=op.op_id, code="not_found", message=str(exc)))

        return {"ack": ack, "id_map": id_map, "errors": errors}

    def _apply_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        if op.entity not in self.allowed_entities:
            raise ValueError(f"Unsupported entity: {op.entity}")
        if op.op not in self.allowed_ops:
            raise ValueError(f"Unsupported op: {op.op}")

        if op.entity == "task":
            self._apply_task_op(user_id, op, id_map)
        elif op.entity == "subtask":
            self._apply_subtask_op(user_id, op, id_map)
        elif op.entity == "tag":
            self._apply_tag_op(user_id, op, id_map)

    def _apply_task_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        if op.op == "create":
            if not op.data or not op.data.title:
                raise ValueError("Task create requires title")
            if op.client_id:
                existing = self.task_repository.get_by_client_id(user_id, op.client_id, include_deleted=True)
                if existing:
                    id_map["task"].append(SyncIdMap(client_id=op.client_id, id=existing.id))
                    return
            task = self.task_repository.create(
                op.data.title,
                op.data.description,
                user_id,
                client_id=op.client_id,
            )
            self.sync_event_service.log_task_event(user_id, task.id, "create")
            if op.client_id:
                id_map["task"].append(SyncIdMap(client_id=op.client_id, id=task.id))
            return

        task = self._resolve_task(user_id, op)
        if op.op == "update":
            data = op.data or SyncOpData()
            updated = self.task_repository.update(
                task,
                data.title,
                data.description,
                data.is_completed,
            )
            self.sync_event_service.log_task_event(user_id, updated.id, "update")
            return
        if op.op == "delete":
            deleted = self.task_repository.delete(task)
            self.sync_event_service.log_task_event(user_id, deleted.id, "delete")
            return

    def _apply_subtask_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        if op.op == "create":
            if not op.data or not op.data.text:
                raise ValueError("Subtask create requires text")
            task_id = op.data.task_id
            if task_id is None and op.data.task_client_id:
                task = self.task_repository.get_by_client_id(user_id, op.data.task_client_id, include_deleted=True)
                if not task:
                    raise LookupError("Task not found for subtask create")
                task_id = task.id
            if task_id is None:
                raise ValueError("Subtask create requires task_id or task_client_id")
            subtask = self.subtask_repository.create(
                task_id,
                op.data.text,
                op.data.is_completed or False,
                client_id=op.client_id,
            )
            self.sync_event_service.log_subtask_event(user_id, subtask.id, "create")
            if op.client_id:
                id_map["subtask"].append(SyncIdMap(client_id=op.client_id, id=subtask.id))
            return

        subtask = self._resolve_subtask(op)
        if op.op == "update":
            data = op.data or SyncOpData()
            updated = self.subtask_repository.update(subtask, data.text, data.is_completed)
            self.sync_event_service.log_subtask_event(user_id, updated.id, "update")
            return
        if op.op == "delete":
            deleted = self.subtask_repository.delete(subtask)
            self.sync_event_service.log_subtask_event(user_id, deleted.id, "delete")
            return

    def _apply_tag_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        if op.op == "create":
            data = op.data
            if not data:
                raise ValueError("Tag create requires data")
            if op.client_id:
                existing = self.tag_repository.get_by_client_id(user_id, op.client_id, include_deleted=True)
                if existing:
                    id_map["tag"].append(SyncIdMap(client_id=op.client_id, id=existing.id))
                    return
            tag = self.tag_repository.create(
                user_id,
                bool(data.is_user_tag) if data.is_user_tag is not None else True,
                data.name,
                data.color,
                client_id=op.client_id,
            )
            self.sync_event_service.log_tag_event(user_id, tag.id, "create")
            if op.client_id:
                id_map["tag"].append(SyncIdMap(client_id=op.client_id, id=tag.id))
            return

        tag = self._resolve_tag(user_id, op)
        if op.op == "update":
            data = op.data or SyncOpData()
            updated = self.tag_repository.update(
                tag,
                bool(data.is_user_tag) if data.is_user_tag is not None else tag.is_user_tag,
                data.name if data.name is not None else tag.name,
                data.color if data.color is not None else tag.color,
            )
            self.sync_event_service.log_tag_event(user_id, updated.id, "update")
            return
        if op.op == "delete":
            deleted = self.tag_repository.delete(tag)
            self.sync_event_service.log_tag_event(user_id, deleted.id, "delete")
            return

    def _resolve_task(self, user_id: UUID, op: SyncOpInput):
        if op.id is not None:
            task = self.task_repository.get_by_id_and_user_id(op.id, user_id, include_deleted=True)
        elif op.client_id is not None:
            task = self.task_repository.get_by_client_id(user_id, op.client_id, include_deleted=True)
        else:
            raise ValueError("Task op requires id or client_id")
        if not task:
            raise LookupError("Task not found")
        return task

    def _resolve_subtask(self, op: SyncOpInput):
        if op.id is not None:
            subtask = self.subtask_repository.get_by_id(op.id, include_deleted=True)
        elif op.client_id is not None:
            subtask = self.subtask_repository.get_by_client_id(op.client_id, include_deleted=True)
        else:
            raise ValueError("Subtask op requires id or client_id")
        if not subtask:
            raise LookupError("Subtask not found")
        return subtask

    def _resolve_tag(self, user_id: UUID, op: SyncOpInput):
        if op.id is not None:
            tag = self.tag_repository.get_by_id(user_id, op.id, include_deleted=True)
        elif op.client_id is not None:
            tag = self.tag_repository.get_by_client_id(user_id, op.client_id, include_deleted=True)
        else:
            raise ValueError("Tag op requires id or client_id")
        if not tag:
            raise LookupError("Tag not found")
        return tag
