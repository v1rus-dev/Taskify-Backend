from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task import Task
from app.schemas import TaskCreate, TaskRead
from typing import List

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/create", response_model=TaskRead)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(
        title = task.title,
        description = task.description,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/", response_model=List[TaskRead])
def get_tasks(db: Session = Depends(get_db)):
    tasks =  db.query(Task).all()
    return tasks