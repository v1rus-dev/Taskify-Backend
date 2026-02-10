from __future__ import annotations

from typing import Optional, List
from uuid import UUID

from app.repositories.sync_event_repository import SyncEventRepository
from app.models.task import Task
from app.models.subtask import SubTask
from app.models.tag import Tag
from app.models.space import Space
from app.models.space_member import SpaceMember
from app.models.space_invite import SpaceInvite
from app.models.space_task import SpaceTask
from app.models.space_subtask import SpaceSubTask
from app.models.space_task_list import SpaceTaskList
from app.models.space_note import SpaceNote
from app.schemas import (
    TaskRead,
    SubTaskRead,
    TagRead,
    SpaceRead,
    SpaceMemberRead,
    SpaceInviteRead,
    SpaceTaskRead,
    SpaceSubTaskRead,
    SpaceListRead,
    SpaceNoteRead,
)


class SyncEventService:
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

    def __init__(self, sync_event_repository: SyncEventRepository):
        self.sync_event_repository = sync_event_repository

    def log_event(
        self,
        user_id: UUID,
        entity: str,
        entity_id: int,
        op: str,
    ) -> None:
        if entity not in self.allowed_entities:
            raise ValueError(f"Unsupported entity for sync event: {entity}")
        if op not in self.allowed_ops:
            raise ValueError(f"Unsupported op for sync event: {op}")
        self.sync_event_repository.create(user_id, entity, entity_id, op)

    def log_task_event(self, user_id: UUID, task_id: int, op: str) -> None:
        self.log_event(user_id, "task", int(task_id), op)

    def log_subtask_event(self, user_id: UUID, subtask_id: int, op: str) -> None:
        self.log_event(user_id, "subtask", int(subtask_id), op)

    def log_tag_event(self, user_id: UUID, tag_id: int, op: str) -> None:
        self.log_event(user_id, "tag", int(tag_id), op)

    def log_space_event(self, user_id: UUID, space_id: int, op: str) -> None:
        self.log_event(user_id, "space", int(space_id), op)

    def log_space_member_event(self, user_id: UUID, member_id: int, op: str) -> None:
        self.log_event(user_id, "space_member", int(member_id), op)

    def log_space_invite_event(self, user_id: UUID, invite_id: int, op: str) -> None:
        self.log_event(user_id, "space_invite", int(invite_id), op)

    def log_space_task_event(self, user_id: UUID, task_id: int, op: str) -> None:
        self.log_event(user_id, "space_task", int(task_id), op)

    def log_space_subtask_event(self, user_id: UUID, subtask_id: int, op: str) -> None:
        self.log_event(user_id, "space_subtask", int(subtask_id), op)

    def log_space_list_event(self, user_id: UUID, list_id: int, op: str) -> None:
        self.log_event(user_id, "space_list", int(list_id), op)

    def log_space_note_event(self, user_id: UUID, note_id: int, op: str) -> None:
        self.log_event(user_id, "space_note", int(note_id), op)

    def get_changes(self, user_id: UUID, cursor: int, limit: int) -> List:
        return self.sync_event_repository.list_changes(user_id, cursor, limit)

    def build_changes(self, user_id: UUID, events: List) -> List[dict]:
        db = self.sync_event_repository.db
        changes: List[dict] = []
        for event in events:
            data = None
            if event.entity == "task":
                task = (
                    db.query(Task)
                    .filter(Task.id == event.entity_id, Task.user_id == user_id)
                    .first()
                )
                if task:
                    data = TaskRead.model_validate(task).model_dump()
            elif event.entity == "subtask":
                subtask = db.query(SubTask).filter(SubTask.id == event.entity_id).first()
                if subtask:
                    data = SubTaskRead.model_validate(subtask).model_dump()
            elif event.entity == "tag":
                tag = (
                    db.query(Tag)
                    .filter(Tag.user_id == user_id, Tag.id == event.entity_id)
                    .first()
                )
                if tag:
                    data = TagRead.model_validate(tag).model_dump()
            elif event.entity == "space":
                space = db.query(Space).filter(Space.id == event.entity_id).first()
                if space:
                    data = SpaceRead.model_validate(space).model_dump()
            elif event.entity == "space_member":
                member = db.query(SpaceMember).filter(SpaceMember.id == event.entity_id).first()
                if member:
                    data = SpaceMemberRead.model_validate(member).model_dump()
            elif event.entity == "space_invite":
                invite = db.query(SpaceInvite).filter(SpaceInvite.id == event.entity_id).first()
                if invite:
                    data = SpaceInviteRead.model_validate(invite).model_dump()
            elif event.entity == "space_task":
                task = db.query(SpaceTask).filter(SpaceTask.id == event.entity_id).first()
                if task:
                    data = SpaceTaskRead.model_validate(task).model_dump()
            elif event.entity == "space_subtask":
                subtask = db.query(SpaceSubTask).filter(SpaceSubTask.id == event.entity_id).first()
                if subtask:
                    data = SpaceSubTaskRead.model_validate(subtask).model_dump()
            elif event.entity == "space_list":
                task_list = db.query(SpaceTaskList).filter(SpaceTaskList.id == event.entity_id).first()
                if task_list:
                    data = SpaceListRead.model_validate(task_list).model_dump()
            elif event.entity == "space_note":
                note = db.query(SpaceNote).filter(SpaceNote.id == event.entity_id).first()
                if note:
                    data = SpaceNoteRead.model_validate(note).model_dump()

            changes.append(
                {
                    "id": event.id,
                    "entity": event.entity,
                    "entity_id": event.entity_id,
                    "op": event.op,
                    "occurred_at": event.occurred_at,
                    "data": data,
                }
            )
        return changes
