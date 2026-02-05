from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.subtask import SubTask


class SubTaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, task_id: int, text: str, is_completed: bool = False, client_id: Optional[UUID] = None) -> SubTask:
        """Создаёт новую подзадачу."""
        new_subtask = SubTask(
            task_id=task_id,
            text=text,
            is_completed=is_completed,
            client_id=client_id,
        )
        self.db.add(new_subtask)
        self.db.commit()
        self.db.refresh(new_subtask)
        return new_subtask

    def get_by_task_id(self, task_id: int, include_deleted: bool = False) -> List[SubTask]:
        """Получает все подзадачи для задачи."""
        query = self.db.query(SubTask).filter(SubTask.task_id == task_id)
        if not include_deleted:
            query = query.filter(SubTask.deleted_at.is_(None))
        return query.all()

    def get_by_id(self, subtask_id: int, include_deleted: bool = False) -> Optional[SubTask]:
        """Получает подзадачу по ID."""
        query = self.db.query(SubTask).filter(SubTask.id == subtask_id)
        if not include_deleted:
            query = query.filter(SubTask.deleted_at.is_(None))
        return query.first()

    def get_by_client_id(self, client_id: UUID, include_deleted: bool = True) -> Optional[SubTask]:
        query = self.db.query(SubTask).filter(SubTask.client_id == client_id)
        if not include_deleted:
            query = query.filter(SubTask.deleted_at.is_(None))
        return query.first()

    def get_by_id_and_task_id(self, subtask_id: int, task_id: int, include_deleted: bool = False) -> Optional[SubTask]:
        """Получает подзадачу по ID и task_id."""
        query = self.db.query(SubTask).filter(
            SubTask.id == subtask_id,
            SubTask.task_id == task_id
        )
        if not include_deleted:
            query = query.filter(SubTask.deleted_at.is_(None))
        return query.first()

    def update(self, subtask: SubTask, text: Optional[str] = None, is_completed: Optional[bool] = None) -> SubTask:
        """Обновляет подзадачу."""
        if text is not None:
            subtask.text = text
        if is_completed is not None:
            subtask.is_completed = is_completed
        self.db.commit()
        self.db.refresh(subtask)
        return subtask

    def delete(self, subtask: SubTask) -> SubTask:
        """Мягко удаляет подзадачу."""
        subtask.deleted_at = func.now()
        self.db.commit()
        self.db.refresh(subtask)
        return subtask
