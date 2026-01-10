from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas import TaskCreate, TaskRead
from app.utils.tasks import enrich_tasks_with_favorite
from typing import List
from uuid import UUID

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/create", response_model=TaskRead)
def create_task(user_id: UUID, task: TaskCreate, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_task = Task(
        title=task.title,
        description=task.description,
        user_id=user_id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    # Обогащаем задачу информацией об избранном
    enriched = enrich_tasks_with_favorite([new_task], user_id, db)
    return enriched[0]

@router.get("/", response_model=List[TaskRead])
def get_tasks(user_id: UUID, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return enrich_tasks_with_favorite(tasks, user_id, db)

@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, user_id: UUID, task: TaskCreate, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    existing_task.title = task.title
    existing_task.description = task.description
    if task.is_completed is not None:
        existing_task.is_completed = task.is_completed
    db.commit()
    db.refresh(existing_task)
    
    # Обогащаем задачу информацией об избранном
    enriched = enrich_tasks_with_favorite([existing_task], user_id, db)
    return enriched[0]

@router.delete("/{task_id}")
def delete_task(task_id: int, user_id: UUID, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(existing_task)
    db.commit()
    return {"message": "Task deleted successfully"}