from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas import TaskCreate, TaskRead
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
    return new_task

@router.get("/", response_model=List[TaskRead])
def get_tasks(user_id: UUID, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return tasks