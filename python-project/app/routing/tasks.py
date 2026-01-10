from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.depends import get_task_service
from app.services.task_service import TaskService
from app.schemas import TaskCreate, TaskRead
from typing import List
from uuid import UUID

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/create", response_model=TaskRead)
def create_task(
    user_id: UUID,
    task: TaskCreate,
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.create_task(user_id, task.title, task.description)

@router.get("/", response_model=List[TaskRead])
def get_tasks(
    user_id: UUID,
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.get_tasks(user_id)

@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    user_id: UUID,
    task: TaskCreate,
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.update_task(task_id, user_id, task.title, task.description, task.is_completed)

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    user_id: UUID,
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.delete_task(task_id, user_id)
