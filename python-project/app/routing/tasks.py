from fastapi import APIRouter, Depends
from app.depends import get_task_service, get_current_user
from app.services.task_service import TaskService
from app.schemas import TaskCreate, TaskUpdate, TaskRead
from typing import List
from app.models.user import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/create", response_model=TaskRead)
def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.create_task(current_user.id, task.title, task.description)

@router.get("/", response_model=List[TaskRead])
def get_tasks(
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.get_tasks(current_user.id)

@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    task: TaskUpdate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.update_task(task_id, current_user.id, task.title, task.description, task.is_completed)

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.delete_task(task_id, current_user.id)
