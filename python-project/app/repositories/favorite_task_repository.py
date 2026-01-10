from typing import List
from sqlalchemy.orm import Session
from app.models.favorite_task import FavoriteTask
from app.models.task import Task
from uuid import UUID


class FavoriteTaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, task_id: int, user_id: UUID) -> FavoriteTask:
        """Добавляет задачу в избранное."""
        favorite_task = FavoriteTask(task_id=task_id, user_id=user_id)
        self.db.add(favorite_task)
        self.db.commit()
        self.db.refresh(favorite_task)
        return favorite_task

    def get_favorite_task_ids_by_user_id(self, user_id: UUID) -> set:
        """Получает множество ID избранных задач пользователя."""
        favorite_task_ids = self.db.query(FavoriteTask.task_id).filter(
            FavoriteTask.user_id == user_id
        ).all()
        return {task_id[0] for task_id in favorite_task_ids}

    def get_favorite_task_ids_by_user_id_and_task_ids(self, user_id: UUID, task_ids: List[int]) -> set:
        """Получает множество ID избранных задач пользователя из указанного списка."""
        if not task_ids:
            return set()
        favorite_task_ids = self.db.query(FavoriteTask.task_id).filter(
            FavoriteTask.user_id == user_id,
            FavoriteTask.task_id.in_(task_ids)
        ).all()
        return {task_id[0] for task_id in favorite_task_ids}

    def get_favorite_tasks_by_user_id(self, user_id: UUID) -> List[Task]:
        """Получает все избранные задачи пользователя."""
        return self.db.query(Task).join(
            FavoriteTask, Task.id == FavoriteTask.task_id
        ).filter(
            FavoriteTask.user_id == user_id
        ).all()
