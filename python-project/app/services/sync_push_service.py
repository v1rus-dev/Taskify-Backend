from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from app.models.space import Space
from app.models.space_invite import SpaceInvite
from app.models.space_member import SpaceMember
from app.models.space_note import SpaceNote
from app.models.space_subtask import SpaceSubTask
from app.models.space_task import SpaceTask
from app.models.space_task_list import SpaceTaskList
from app.repositories.task_repository import TaskRepository
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.user_repository import UserRepository
from app.repositories.sync_op_repository import SyncOpRepository
from app.repositories.space_repository import SpaceRepository
from app.repositories.space_invite_repository import SpaceInviteRepository
from app.repositories.space_content_repository import SpaceContentRepository
from app.services.sync_event_service import SyncEventService
from app.schemas import SyncOpInput, SyncOpError, SyncIdMap, SyncOpData


class SyncPushService:
    allowed_entities = {
        "task",
        "subtask",
        "tag",
        "space",
        "space_member",
        "space_invite",
        "space_task",
        "space_subtask",
        "space_list",
        "space_note",
    }
    allowed_ops = {"create", "update", "delete"}

    def __init__(
        self,
        task_repository: TaskRepository,
        subtask_repository: SubTaskRepository,
        tag_repository: TagRepository,
        user_repository: UserRepository,
        sync_op_repository: SyncOpRepository,
        sync_event_service: SyncEventService,
        space_repository: SpaceRepository,
        space_invite_repository: SpaceInviteRepository,
        space_content_repository: SpaceContentRepository,
    ):
        self.task_repository = task_repository
        self.subtask_repository = subtask_repository
        self.tag_repository = tag_repository
        self.user_repository = user_repository
        self.sync_op_repository = sync_op_repository
        self.sync_event_service = sync_event_service
        self.space_repository = space_repository
        self.space_invite_repository = space_invite_repository
        self.space_content_repository = space_content_repository

    def process(self, user_id: UUID, device_id: Optional[str], ops: List[SyncOpInput]):
        self.user_repository.ensure_user_exists(user_id)
        id_map: Dict[str, List[SyncIdMap]] = {
            "task": [],
            "subtask": [],
            "tag": [],
            "space": [],
            "space_member": [],
            "space_invite": [],
            "space_task": [],
            "space_subtask": [],
            "space_list": [],
            "space_note": [],
        }
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
        elif op.entity == "space":
            self._apply_space_op(user_id, op, id_map)
        elif op.entity == "space_member":
            self._apply_space_member_op(user_id, op, id_map)
        elif op.entity == "space_invite":
            self._apply_space_invite_op(user_id, op, id_map)
        elif op.entity == "space_list":
            self._apply_space_list_op(user_id, op, id_map)
        elif op.entity == "space_task":
            self._apply_space_task_op(user_id, op, id_map)
        elif op.entity == "space_subtask":
            self._apply_space_subtask_op(user_id, op, id_map)
        elif op.entity == "space_note":
            self._apply_space_note_op(user_id, op, id_map)

    def _apply_task_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        if op.op == "create":
            if not op.data or not op.data.title:
                raise ValueError("Task create requires title")
            if op.client_id:
                existing = self.task_repository.get_by_client_id(user_id, op.client_id, include_deleted=True)
                if existing:
                    id_map["task"].append(SyncIdMap(client_id=op.client_id, id=existing.id))
                    return
            task = self.task_repository.create(op.data.title, op.data.description, user_id, client_id=op.client_id)
            self.sync_event_service.log_task_event(user_id, task.id, "create")
            if op.client_id:
                id_map["task"].append(SyncIdMap(client_id=op.client_id, id=task.id))
            return

        task = self._resolve_task(user_id, op)
        if op.op == "update":
            data = op.data or SyncOpData()
            updated = self.task_repository.update(task, data.title, data.description, data.is_completed)
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
            subtask = self.subtask_repository.create(task_id, op.data.text, op.data.is_completed or False, client_id=op.client_id)
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

    def _apply_space_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        data = op.data or SyncOpData()
        if op.op == "create":
            if not data.name:
                raise ValueError("Space create requires name")
            if op.client_id:
                existing = self.space_repository.get_space_by_client_id(op.client_id)
                if existing:
                    id_map["space"].append(SyncIdMap(client_id=op.client_id, id=existing.id))
                    return
            space = self.space_repository.create_space(
                name=data.name,
                description=data.description,
                created_by=user_id,
                is_lightweight=bool(data.is_lightweight) if data.is_lightweight is not None else False,
                client_id=op.client_id,
            )
            self.space_repository.activate_or_create_member(space.id, user_id, "owner")
            self.sync_event_service.log_space_event(user_id, space.id, "create")
            if op.client_id:
                id_map["space"].append(SyncIdMap(client_id=op.client_id, id=space.id))
            return

        space = self._resolve_space(op)
        if op.op == "update":
            if data.name is not None:
                space.name = data.name
            if data.description is not None:
                space.description = data.description
            if data.is_lightweight is not None:
                space.is_lightweight = data.is_lightweight
            self.space_repository.db.commit()
            self.space_repository.db.refresh(space)
            self.sync_event_service.log_space_event(user_id, space.id, "update")
            return
        if op.op == "delete":
            self.space_repository.delete_space(space)
            self.sync_event_service.log_space_event(user_id, space.id, "delete")

    def _apply_space_member_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        data = op.data or SyncOpData()
        if op.op == "create":
            if data.space_id is None or data.user_id is None or data.role is None:
                raise ValueError("Space member create requires space_id, user_id and role")
            member = self.space_repository.activate_or_create_member(data.space_id, data.user_id, data.role)
            self.sync_event_service.log_space_member_event(user_id, member.id, "create")
            return

        member = self._resolve_space_member(op)
        if op.op == "update":
            if data.role is not None:
                member.role = data.role
            if data.status is not None:
                member.status = data.status
            self.space_repository.db.commit()
            self.space_repository.db.refresh(member)
            self.sync_event_service.log_space_member_event(user_id, member.id, "update")
            return
        if op.op == "delete":
            member.status = "removed"
            self.space_repository.db.commit()
            self.space_repository.db.refresh(member)
            self.sync_event_service.log_space_member_event(user_id, member.id, "delete")

    def _apply_space_invite_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        data = op.data or SyncOpData()
        if op.op == "create":
            if data.space_id is None or data.role is None or data.expires_at is None or data.token is None:
                raise ValueError("Space invite create requires space_id, role, token, expires_at")
            invite = self.space_invite_repository.create_invite(data.space_id, user_id, data.role, data.token, data.expires_at)
            self.sync_event_service.log_space_invite_event(user_id, invite.id, "create")
            return

        invite = self._resolve_space_invite(op)
        if op.op == "update":
            if data.status is not None:
                invite.status = data.status
            if data.role is not None:
                invite.role = data.role
            self.space_invite_repository.db.commit()
            self.space_invite_repository.db.refresh(invite)
            self.sync_event_service.log_space_invite_event(user_id, invite.id, "update")
            return
        if op.op == "delete":
            invite.status = "revoked"
            self.space_invite_repository.db.commit()
            self.space_invite_repository.db.refresh(invite)
            self.sync_event_service.log_space_invite_event(user_id, invite.id, "delete")

    def _apply_space_list_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        data = op.data or SyncOpData()
        if op.op == "create":
            if data.space_id is None or data.title is None:
                raise ValueError("Space list create requires space_id and title")
            if op.client_id:
                existing = self.space_content_repository.get_list_by_client_id(data.space_id, op.client_id)
                if existing:
                    id_map["space_list"].append(SyncIdMap(client_id=op.client_id, id=existing.id))
                    return
            row = self.space_content_repository.create_list(data.space_id, data.title, data.order or 0, user_id, client_id=op.client_id)
            self.sync_event_service.log_space_list_event(user_id, row.id, "create")
            if op.client_id:
                id_map["space_list"].append(SyncIdMap(client_id=op.client_id, id=row.id))
            return

        row = self._resolve_space_list(op)
        if op.op == "update":
            updated = self.space_content_repository.update_list(row, data.title, data.order, user_id)
            self.sync_event_service.log_space_list_event(user_id, updated.id, "update")
            return
        if op.op == "delete":
            row_id = row.id
            self.space_content_repository.delete_list(row)
            self.sync_event_service.log_space_list_event(user_id, row_id, "delete")

    def _apply_space_task_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        data = op.data or SyncOpData()
        if op.op == "create":
            if data.space_id is None or data.title is None:
                raise ValueError("Space task create requires space_id and title")
            if op.client_id:
                existing = self.space_content_repository.get_task_by_client_id(data.space_id, op.client_id)
                if existing:
                    id_map["space_task"].append(SyncIdMap(client_id=op.client_id, id=existing.id))
                    return
            row = self.space_content_repository.create_task(
                data.space_id,
                data.list_id,
                data.title,
                data.description,
                data.assignee_id,
                user_id,
                client_id=op.client_id,
            )
            self.sync_event_service.log_space_task_event(user_id, row.id, "create")
            if op.client_id:
                id_map["space_task"].append(SyncIdMap(client_id=op.client_id, id=row.id))
            return

        row = self._resolve_space_task(op)
        if op.op == "update":
            updated = self.space_content_repository.update_task(
                row,
                user_id,
                list_id=data.list_id,
                title=data.title,
                description=data.description,
                assignee_id=data.assignee_id,
                claimed_by_id=data.claimed_by_id,
            )
            if data.is_completed is not None:
                updated = self.space_content_repository.set_task_completed(updated, data.is_completed, user_id)
            self.sync_event_service.log_space_task_event(user_id, updated.id, "update")
            return
        if op.op == "delete":
            deleted = self.space_content_repository.delete_task(row, user_id)
            self.sync_event_service.log_space_task_event(user_id, deleted.id, "delete")

    def _apply_space_subtask_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        data = op.data or SyncOpData()
        if op.op == "create":
            if data.task_id is None or data.title is None:
                raise ValueError("Space subtask create requires task_id and title")
            if op.client_id:
                existing = self.space_content_repository.get_subtask_by_client_id(data.task_id, op.client_id)
                if existing:
                    id_map["space_subtask"].append(SyncIdMap(client_id=op.client_id, id=existing.id))
                    return
            row = self.space_content_repository.create_subtask(data.task_id, data.title, bool(data.is_completed), user_id, client_id=op.client_id)
            self.sync_event_service.log_space_subtask_event(user_id, row.id, "create")
            if op.client_id:
                id_map["space_subtask"].append(SyncIdMap(client_id=op.client_id, id=row.id))
            return

        row = self._resolve_space_subtask(op)
        if op.op == "update":
            updated = self.space_content_repository.update_subtask(row, user_id, data.title, data.is_completed)
            self.sync_event_service.log_space_subtask_event(user_id, updated.id, "update")
            return
        if op.op == "delete":
            deleted = self.space_content_repository.delete_subtask(row, user_id)
            self.sync_event_service.log_space_subtask_event(user_id, deleted.id, "delete")

    def _apply_space_note_op(self, user_id: UUID, op: SyncOpInput, id_map: Dict[str, List[SyncIdMap]]):
        data = op.data or SyncOpData()
        if op.op == "create":
            if data.space_id is None or data.title is None or data.body is None:
                raise ValueError("Space note create requires space_id, title and body")
            if op.client_id:
                existing = self.space_content_repository.get_note_by_client_id(data.space_id, op.client_id)
                if existing:
                    id_map["space_note"].append(SyncIdMap(client_id=op.client_id, id=existing.id))
                    return
            row = self.space_content_repository.create_note(data.space_id, data.title, data.body, user_id, client_id=op.client_id)
            self.sync_event_service.log_space_note_event(user_id, row.id, "create")
            if op.client_id:
                id_map["space_note"].append(SyncIdMap(client_id=op.client_id, id=row.id))
            return

        row = self._resolve_space_note(op)
        if op.op == "update":
            updated = self.space_content_repository.update_note(row, user_id, data.title, data.body)
            self.sync_event_service.log_space_note_event(user_id, updated.id, "update")
            return
        if op.op == "delete":
            deleted = self.space_content_repository.delete_note(row, user_id)
            self.sync_event_service.log_space_note_event(user_id, deleted.id, "delete")

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

    def _resolve_space(self, op: SyncOpInput) -> Space:
        if op.id is not None:
            row = self.space_repository.get_space(op.id)
        elif op.client_id is not None:
            row = self.space_repository.get_space_by_client_id(op.client_id)
        else:
            raise ValueError("Space op requires id or client_id")
        if not row:
            raise LookupError("Space not found")
        return row

    def _resolve_space_member(self, op: SyncOpInput) -> SpaceMember:
        if op.id is not None:
            row = self.space_repository.get_member_by_id(op.id)
        else:
            data = op.data or SyncOpData()
            if data.space_id is None or data.user_id is None:
                raise ValueError("Space member op requires id or (space_id and user_id)")
            row = self.space_repository.get_member(data.space_id, data.user_id)
        if not row:
            raise LookupError("Space member not found")
        return row

    def _resolve_space_invite(self, op: SyncOpInput) -> SpaceInvite:
        if op.id is not None:
            row = self.space_invite_repository.get_invite(op.id)
        elif op.data and op.data.token:
            row = self.space_invite_repository.get_by_token(op.data.token)
        else:
            raise ValueError("Space invite op requires id or token")
        if not row:
            raise LookupError("Space invite not found")
        return row

    def _resolve_space_list(self, op: SyncOpInput) -> SpaceTaskList:
        data = op.data or SyncOpData()
        if data.space_id is None:
            raise ValueError("Space list op requires data.space_id")
        if op.id is not None:
            row = self.space_content_repository.get_list(data.space_id, op.id)
        elif op.client_id is not None:
            row = self.space_content_repository.get_list_by_client_id(data.space_id, op.client_id)
        else:
            raise ValueError("Space list op requires id or client_id")
        if not row:
            raise LookupError("Space list not found")
        return row

    def _resolve_space_task(self, op: SyncOpInput) -> SpaceTask:
        data = op.data or SyncOpData()
        if data.space_id is None:
            raise ValueError("Space task op requires data.space_id")
        if op.id is not None:
            row = self.space_content_repository.get_task(data.space_id, op.id, include_deleted=True)
        elif op.client_id is not None:
            row = self.space_content_repository.get_task_by_client_id(data.space_id, op.client_id, include_deleted=True)
        else:
            raise ValueError("Space task op requires id or client_id")
        if not row:
            raise LookupError("Space task not found")
        return row

    def _resolve_space_subtask(self, op: SyncOpInput) -> SpaceSubTask:
        data = op.data or SyncOpData()
        if data.task_id is None:
            raise ValueError("Space subtask op requires data.task_id")
        if op.id is not None:
            row = self.space_content_repository.get_subtask(data.task_id, op.id, include_deleted=True)
        elif op.client_id is not None:
            row = self.space_content_repository.get_subtask_by_client_id(data.task_id, op.client_id, include_deleted=True)
        else:
            raise ValueError("Space subtask op requires id or client_id")
        if not row:
            raise LookupError("Space subtask not found")
        return row

    def _resolve_space_note(self, op: SyncOpInput) -> SpaceNote:
        data = op.data or SyncOpData()
        if data.space_id is None:
            raise ValueError("Space note op requires data.space_id")
        if op.id is not None:
            row = self.space_content_repository.get_note(data.space_id, op.id, include_deleted=True)
        elif op.client_id is not None:
            row = self.space_content_repository.get_note_by_client_id(data.space_id, op.client_id, include_deleted=True)
        else:
            raise ValueError("Space note op requires id or client_id")
        if not row:
            raise LookupError("Space note not found")
        return row
