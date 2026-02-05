from fastapi import APIRouter, Depends
from app.depends import get_task_service, get_current_user
from app.services.task_service import TaskService
from app.schemas import TaskCreate, TaskUpdate, TaskRead
from typing import List
from app.models.user import User
from app.routing.docs import error_response

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post(
    "/create",
    response_model=TaskRead,
    summary="Create task",
    description="Creates a new task for the current user.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("USER_NOT_FOUND", "User not found", "User not found."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.create_task(current_user.id, task.title, task.description, task.tags)

@router.get(
    "/",
    response_model=List[TaskRead],
    summary="List tasks",
    description="Returns tasks for the current user.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("USER_NOT_FOUND", "User not found", "User not found."),
    },
)
def get_tasks(
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.get_tasks(current_user.id, include_deleted=include_deleted)

@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update task",
    description="Updates an existing task.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("TASK_NOT_FOUND", "Task not found", "Task not found."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def update_task(
    task_id: int,
    task: TaskUpdate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.update_task(
        task_id,
        current_user.id,
        task.title,
        task.description,
        task.is_completed,
        task.tags,
    )

@router.delete(
    "/{task_id}",
    response_model=TaskRead,
    summary="Delete task",
    description="Soft-deletes a task.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("TASK_NOT_FOUND", "Task not found", "Task not found."),
    },
)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    return task_service.delete_task(task_id, current_user.id)
