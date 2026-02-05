from fastapi import APIRouter, Depends
from app.depends import get_subtask_service, get_current_user
from app.services.subtask_service import SubTaskService
from app.schemas import SubTaskCreateList, SubTaskRead, SubTaskUpdateList
from typing import List
from app.models.user import User
from app.routing.docs import error_response

router = APIRouter(prefix="/tasks/{task_id}/subtasks", tags=["SubTasks"])


@router.post(
    "",
    response_model=List[SubTaskRead],
    summary="Create subtasks",
    description="Creates multiple subtasks for a task.",
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
def create_subtasks(
    task_id: int,
    payload: SubTaskCreateList,
    current_user: User = Depends(get_current_user),
    subtask_service: SubTaskService = Depends(get_subtask_service)
):
    subtasks_data = [
        {
            "text": st.text,
            "is_completed": st.is_completed if st.is_completed is not None else False
        }
        for st in payload.subtasks
    ]
    return subtask_service.create_subtasks(task_id, current_user.id, subtasks_data)


@router.get(
    "",
    response_model=List[SubTaskRead],
    summary="List subtasks",
    description="Returns subtasks for a task.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("TASK_NOT_FOUND", "Task not found", "Task not found."),
    },
)
def get_subtasks(
    task_id: int,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    subtask_service: SubTaskService = Depends(get_subtask_service)
):
    return subtask_service.get_subtasks(task_id, current_user.id, include_deleted=include_deleted)


@router.patch(
    "",
    response_model=List[SubTaskRead],
    summary="Update subtasks",
    description="Updates multiple subtasks for a task.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("SUBTASK_NOT_FOUND", "SubTask not found", "Subtask or task not found."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def update_subtasks(
    task_id: int,
    payload: SubTaskUpdateList,
    current_user: User = Depends(get_current_user),
    subtask_service: SubTaskService = Depends(get_subtask_service)
):
    subtasks_data = [
        {"id": st.id, "text": st.text, "is_completed": st.is_completed}
        for st in payload.subtasks
    ]
    return subtask_service.update_subtasks(task_id, current_user.id, subtasks_data)


@router.delete(
    "/{subtask_id}",
    summary="Delete subtask",
    description="Deletes a subtask.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("SUBTASK_NOT_FOUND", "SubTask not found", "Subtask or task not found."),
    },
)
def delete_subtask(
    task_id: int,
    subtask_id: int,
    current_user: User = Depends(get_current_user),
    subtask_service: SubTaskService = Depends(get_subtask_service)
):
    return subtask_service.delete_subtask(subtask_id, task_id, current_user.id)
