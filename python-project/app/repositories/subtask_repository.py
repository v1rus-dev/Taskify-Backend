from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.subtask import SubTask


class SubTaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, task_id: int, text: str, is_completed: bool = False) -> SubTask:
        """Создаёт новую подзадачу."""
        new_subtask = SubTask(
            task_id=task_id,
            text=text,
            is_completed=is_completed
        )
        self.db.add(new_subtask)
        self.db.commit()
        self.db.refresh(new_subtask)
        return new_subtask

    def get_by_task_id(self, task_id: int) -> List[SubTask]:
        """Получает все подзадачи для задачи."""
        return self.db.query(SubTask).filter(SubTask.task_id == task_id).all()

    def get_by_id(self, subtask_id: int) -> Optional[SubTask]:
        """Получает подзадачу по ID."""
        return self.db.query(SubTask).filter(SubTask.id == subtask_id).first()

    def get_by_id_and_task_id(self, subtask_id: int, task_id: int) -> Optional[SubTask]:
        """Получает подзадачу по ID и task_id."""
        return self.db.query(SubTask).filter(
            SubTask.id == subtask_id,
            SubTask.task_id == task_id
        ).first()

    def update(self, subtask: SubTask, text: Optional[str] = None, is_completed: Optional[bool] = None) -> SubTask:
        """Обновляет подзадачу."""
        if text is not None:
            subtask.text = text
        if is_completed is not None:
            subtask.is_completed = is_completed
        self.db.commit()
        self.db.refresh(subtask)
        return subtask

    def delete(self, subtask: SubTask) -> None:
        """Удаляет подзадачу."""
        self.db.delete(subtask)
        self.db.commit()
