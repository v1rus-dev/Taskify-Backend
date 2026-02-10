from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.space_task_list import SpaceTaskList
from app.models.space_task import SpaceTask
from app.models.space_subtask import SpaceSubTask
from app.models.space_note import SpaceNote


class SpaceContentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_list(self, space_id: int, title: str, order: int, actor_id: UUID, client_id=None) -> SpaceTaskList:
        row = SpaceTaskList(space_id=space_id, title=title, order=order, created_by=actor_id, updated_by=actor_id, client_id=client_id)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_lists(self, space_id: int) -> List[SpaceTaskList]:
        return self.db.query(SpaceTaskList).filter(SpaceTaskList.space_id == space_id).order_by(SpaceTaskList.order.asc(), SpaceTaskList.id.asc()).all()

    def get_list(self, space_id: int, list_id: int) -> Optional[SpaceTaskList]:
        return self.db.query(SpaceTaskList).filter(SpaceTaskList.space_id == space_id, SpaceTaskList.id == list_id).first()

    def get_list_by_client_id(self, space_id: int, client_id) -> Optional[SpaceTaskList]:
        return self.db.query(SpaceTaskList).filter(SpaceTaskList.space_id == space_id, SpaceTaskList.client_id == client_id).first()

    def update_list(self, row: SpaceTaskList, title: Optional[str], order: Optional[int], actor_id: UUID) -> SpaceTaskList:
        if title is not None:
            row.title = title
        if order is not None:
            row.order = order
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return row

    def reorder_lists(self, space_id: int, items: List[dict], actor_id: UUID) -> List[SpaceTaskList]:
        ids = [item["id"] for item in items]
        rows = self.db.query(SpaceTaskList).filter(SpaceTaskList.space_id == space_id, SpaceTaskList.id.in_(ids)).all()
        by_id = {row.id: row for row in rows}
        for item in items:
            row = by_id.get(item["id"])
            if row:
                row.order = item["order"]
                row.updated_by = actor_id
        self.db.commit()
        return self.list_lists(space_id)

    def delete_list(self, row: SpaceTaskList) -> None:
        self.db.delete(row)
        self.db.commit()

    def create_task(self, space_id: int, list_id: Optional[int], title: str, description: Optional[str], assignee_id, actor_id: UUID, client_id=None) -> SpaceTask:
        row = SpaceTask(
            space_id=space_id,
            list_id=list_id,
            title=title,
            description=description,
            assignee_id=assignee_id,
            created_by=actor_id,
            updated_by=actor_id,
            client_id=client_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_tasks(self, space_id: int, include_deleted: bool = False, list_id: Optional[int] = None, assignee_id=None, include_completed: bool = True) -> List[SpaceTask]:
        query = self.db.query(SpaceTask).filter(SpaceTask.space_id == space_id)
        if not include_deleted:
            query = query.filter(SpaceTask.deleted_at.is_(None))
        if list_id is not None:
            query = query.filter(SpaceTask.list_id == list_id)
        if assignee_id is not None:
            query = query.filter(SpaceTask.assignee_id == assignee_id)
        if not include_completed:
            query = query.filter(SpaceTask.completed_at.is_(None))
        return query.order_by(SpaceTask.updated_at.desc()).all()

    def get_task(self, space_id: int, task_id: int, include_deleted: bool = False) -> Optional[SpaceTask]:
        query = self.db.query(SpaceTask).filter(SpaceTask.space_id == space_id, SpaceTask.id == task_id)
        if not include_deleted:
            query = query.filter(SpaceTask.deleted_at.is_(None))
        return query.first()

    def get_task_by_client_id(self, space_id: int, client_id, include_deleted: bool = True) -> Optional[SpaceTask]:
        query = self.db.query(SpaceTask).filter(SpaceTask.space_id == space_id, SpaceTask.client_id == client_id)
        if not include_deleted:
            query = query.filter(SpaceTask.deleted_at.is_(None))
        return query.first()

    def update_task(self, row: SpaceTask, actor_id: UUID, **kwargs) -> SpaceTask:
        for key, value in kwargs.items():
            if value is not None:
                setattr(row, key, value)
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return row

    def set_task_completed(self, row: SpaceTask, is_completed: bool, actor_id: UUID) -> SpaceTask:
        row.completed_at = func.now() if is_completed else None
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_task(self, row: SpaceTask, actor_id: UUID) -> SpaceTask:
        row.deleted_at = func.now()
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return row

    def create_subtask(self, task_id: int, title: str, is_completed: bool, actor_id: UUID, client_id=None) -> SpaceSubTask:
        row = SpaceSubTask(task_id=task_id, title=title, is_completed=is_completed, created_by=actor_id, updated_by=actor_id, client_id=client_id)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_subtasks(self, task_id: int, include_deleted: bool = False) -> List[SpaceSubTask]:
        query = self.db.query(SpaceSubTask).filter(SpaceSubTask.task_id == task_id)
        if not include_deleted:
            query = query.filter(SpaceSubTask.deleted_at.is_(None))
        return query.order_by(SpaceSubTask.created_at.asc()).all()

    def get_subtask(self, task_id: int, subtask_id: int, include_deleted: bool = False) -> Optional[SpaceSubTask]:
        query = self.db.query(SpaceSubTask).filter(SpaceSubTask.task_id == task_id, SpaceSubTask.id == subtask_id)
        if not include_deleted:
            query = query.filter(SpaceSubTask.deleted_at.is_(None))
        return query.first()

    def get_subtask_by_client_id(self, task_id: int, client_id, include_deleted: bool = True) -> Optional[SpaceSubTask]:
        query = self.db.query(SpaceSubTask).filter(SpaceSubTask.task_id == task_id, SpaceSubTask.client_id == client_id)
        if not include_deleted:
            query = query.filter(SpaceSubTask.deleted_at.is_(None))
        return query.first()

    def update_subtask(self, row: SpaceSubTask, actor_id: UUID, title: Optional[str] = None, is_completed: Optional[bool] = None) -> SpaceSubTask:
        if title is not None:
            row.title = title
        if is_completed is not None:
            row.is_completed = is_completed
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_subtask(self, row: SpaceSubTask, actor_id: UUID) -> SpaceSubTask:
        row.deleted_at = func.now()
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return row

    def create_note(self, space_id: int, title: str, body: str, actor_id: UUID, client_id=None) -> SpaceNote:
        row = SpaceNote(space_id=space_id, title=title, body=body, created_by=actor_id, updated_by=actor_id, client_id=client_id)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_notes(self, space_id: int, include_deleted: bool = False) -> List[SpaceNote]:
        query = self.db.query(SpaceNote).filter(SpaceNote.space_id == space_id)
        if not include_deleted:
            query = query.filter(SpaceNote.deleted_at.is_(None))
        return query.order_by(SpaceNote.updated_at.desc()).all()

    def get_note(self, space_id: int, note_id: int, include_deleted: bool = False) -> Optional[SpaceNote]:
        query = self.db.query(SpaceNote).filter(SpaceNote.space_id == space_id, SpaceNote.id == note_id)
        if not include_deleted:
            query = query.filter(SpaceNote.deleted_at.is_(None))
        return query.first()

    def get_note_by_client_id(self, space_id: int, client_id, include_deleted: bool = True) -> Optional[SpaceNote]:
        query = self.db.query(SpaceNote).filter(SpaceNote.space_id == space_id, SpaceNote.client_id == client_id)
        if not include_deleted:
            query = query.filter(SpaceNote.deleted_at.is_(None))
        return query.first()

    def update_note(self, row: SpaceNote, actor_id: UUID, title: Optional[str] = None, body: Optional[str] = None) -> SpaceNote:
        if title is not None:
            row.title = title
        if body is not None:
            row.body = body
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_note(self, row: SpaceNote, actor_id: UUID) -> SpaceNote:
        row.deleted_at = func.now()
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return row
