from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.favorite_task import FavoriteTask
from app.schemas import TaskRead
from uuid import UUID
from typing import List

def enrich_tasks_with_favorite(
    tasks: List[Task], 
    user_id: UUID, 
    db: Session
) -> List[TaskRead]:
    """
    Обогащает список задач информацией о том, является ли каждая задача избранной для пользователя.
    """
    if not tasks:
        return []
    
    # Получаем все ID задач
    task_ids = [task.id for task in tasks]
    
    # Получаем все избранные задачи для этого пользователя из списка
    favorite_task_ids = set(
        db.query(FavoriteTask.task_id)
        .filter(
            FavoriteTask.user_id == user_id,
            FavoriteTask.task_id.in_(task_ids)
        )
        .all()
    )
    # Извлекаем ID из кортежей
    favorite_task_ids = {task_id[0] for task_id in favorite_task_ids}
    
    # Создаём TaskRead объекты с is_favorite
    result = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "is_completed": task.is_completed,
            "user_id": task.user_id,
            "is_favorite": task.id in favorite_task_ids,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        result.append(TaskRead(**task_dict))
    
    return result
