from fastapi import APIRouter, Depends
from app.depends import get_subtask_service, get_current_user
from app.services.subtask_service import SubTaskService
from app.schemas import SubTaskCreateList, SubTaskRead, SubTaskUpdateList
from typing import List
from app.models.user import User

router = APIRouter(prefix="/tasks/{task_id}/subtasks", tags=["SubTasks"])


@router.post("", response_model=List[SubTaskRead])
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


@router.get("", response_model=List[SubTaskRead])
def get_subtasks(
    task_id: int,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    subtask_service: SubTaskService = Depends(get_subtask_service)
):
    return subtask_service.get_subtasks(task_id, current_user.id, include_deleted=include_deleted)


@router.patch("", response_model=List[SubTaskRead])
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


@router.delete("/{subtask_id}")
def delete_subtask(
    task_id: int,
    subtask_id: int,
    current_user: User = Depends(get_current_user),
    subtask_service: SubTaskService = Depends(get_subtask_service)
):
    return subtask_service.delete_subtask(subtask_id, task_id, current_user.id)
