from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.favorite_task import FavoriteTask
from app.models.task import Task
from app.models.user import User
from app.schemas import TaskRead
from typing import List
from uuid import UUID

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.post("/add/{task_id}")
def add_favorite_task(task_id: int, user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    favorite_task = FavoriteTask(task_id=task_id, user_id=user_id)
    db.add(favorite_task)
    db.commit()
    db.refresh(favorite_task)
    return {"message": "Task added to favorites"}

@router.get("/tasks", response_model=List[TaskRead])
def get_favorites_tasks(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Получаем задачи через JOIN с FavoriteTask
    tasks = db.query(Task).join(
        FavoriteTask, Task.id == FavoriteTask.task_id
    ).filter(
        FavoriteTask.user_id == user_id
    ).all()
    
    # Обогащаем задачи информацией об избранном (все будут is_favorite=True)
    from app.utils.tasks import enrich_tasks_with_favorite
    return enrich_tasks_with_favorite(tasks, user_id, db)