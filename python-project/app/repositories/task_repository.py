from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.task import Task
from uuid import UUID


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, title: str, description: Optional[str], user_id: UUID) -> Task:
        """Создаёт новую задачу."""
        new_task = Task(
            title=title,
            description=description,
            user_id=user_id
        )
        self.db.add(new_task)
        self.db.commit()
        self.db.refresh(new_task)
        return new_task

    def get_by_user_id(self, user_id: UUID) -> List[Task]:
        """Получает все задачи пользователя."""
        return self.db.query(Task).filter(Task.user_id == user_id).all()

    def get_by_id_and_user_id(self, task_id: int, user_id: UUID) -> Optional[Task]:
        """Получает задачу по ID и user_id."""
        return self.db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()

    def update(self, task: Task, title: str, description: Optional[str], is_completed: Optional[bool]) -> Task:
        """Обновляет задачу."""
        task.title = title
        task.description = description
        if is_completed is not None:
            task.is_completed = is_completed
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        """Удаляет задачу."""
        self.db.delete(task)
        self.db.commit()
