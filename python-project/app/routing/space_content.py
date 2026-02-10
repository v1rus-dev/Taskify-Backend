from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.depends import (
    get_current_user,
    get_space_list_interactor,
    get_space_task_interactor,
    get_space_note_interactor,
    get_space_interactor,
)
from app.models.user import User
from app.schemas import (
    SpaceListCreate,
    SpaceListUpdate,
    SpaceListRead,
    SpaceListReorderPayload,
    SpaceTaskCreate,
    SpaceTaskUpdate,
    SpaceTaskAssignPayload,
    SpaceTaskCompletePayload,
    SpaceTaskRead,
    SpaceSubTaskCreate,
    SpaceSubTaskUpdate,
    SpaceSubTaskRead,
    SpaceNoteCreate,
    SpaceNoteUpdate,
    SpaceNoteRead,
    ShareCreatePayload,
    ShareCreatedRead,
)
from app.services.space_list_interactor import SpaceListInteractor
from app.services.space_task_interactor import SpaceTaskInteractor
from app.services.space_note_interactor import SpaceNoteInteractor
from app.services.space_interactor import SpaceInteractor


router = APIRouter(tags=["Spaces Content"])


@router.post("/spaces/{space_id}/lists", response_model=SpaceListRead)
def create_list(space_id: int, payload: SpaceListCreate, current_user: User = Depends(get_current_user), interactor: SpaceListInteractor = Depends(get_space_list_interactor)):
    return interactor.create_list(current_user.id, space_id, payload.title, payload.order)


@router.get("/spaces/{space_id}/lists", response_model=List[SpaceListRead])
def list_lists(space_id: int, current_user: User = Depends(get_current_user), interactor: SpaceListInteractor = Depends(get_space_list_interactor)):
    return interactor.list_lists(current_user.id, space_id)


@router.patch("/spaces/{space_id}/lists/{list_id}", response_model=SpaceListRead)
def update_list(space_id: int, list_id: int, payload: SpaceListUpdate, current_user: User = Depends(get_current_user), interactor: SpaceListInteractor = Depends(get_space_list_interactor)):
    return interactor.update_list(current_user.id, space_id, list_id, payload.title, payload.order)


@router.delete("/spaces/{space_id}/lists/{list_id}", status_code=204)
def delete_list(space_id: int, list_id: int, current_user: User = Depends(get_current_user), interactor: SpaceListInteractor = Depends(get_space_list_interactor)):
    interactor.delete_list(current_user.id, space_id, list_id)


@router.post("/spaces/{space_id}/lists/reorder", response_model=List[SpaceListRead])
def reorder_lists(space_id: int, payload: SpaceListReorderPayload, current_user: User = Depends(get_current_user), interactor: SpaceListInteractor = Depends(get_space_list_interactor)):
    items = [item.model_dump() for item in payload.items]
    return interactor.reorder_lists(current_user.id, space_id, items)


@router.post("/spaces/{space_id}/tasks", response_model=SpaceTaskRead)
def create_task(space_id: int, payload: SpaceTaskCreate, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.create_task(current_user.id, space_id, payload.list_id, payload.title, payload.description, payload.assignee_id)


@router.get("/spaces/{space_id}/tasks", response_model=List[SpaceTaskRead])
def list_tasks(
    space_id: int,
    list_id: int | None = Query(default=None),
    assignee_id: UUID | None = Query(default=None),
    include_completed: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    interactor: SpaceTaskInteractor = Depends(get_space_task_interactor),
):
    return interactor.list_tasks(current_user.id, space_id, list_id=list_id, assignee_id=assignee_id, include_completed=include_completed)


@router.get("/spaces/{space_id}/tasks/{task_id}", response_model=SpaceTaskRead)
def get_task(space_id: int, task_id: int, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.get_task(current_user.id, space_id, task_id)


@router.patch("/spaces/{space_id}/tasks/{task_id}", response_model=SpaceTaskRead)
def update_task(space_id: int, task_id: int, payload: SpaceTaskUpdate, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.update_task(
        current_user.id,
        space_id,
        task_id,
        list_id=payload.list_id,
        title=payload.title,
        description=payload.description,
        assignee_id=payload.assignee_id,
    )


@router.delete("/spaces/{space_id}/tasks/{task_id}", response_model=SpaceTaskRead)
def delete_task(space_id: int, task_id: int, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.delete_task(current_user.id, space_id, task_id)


@router.post("/spaces/{space_id}/tasks/{task_id}/claim", response_model=SpaceTaskRead)
def claim_task(space_id: int, task_id: int, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.claim(current_user.id, space_id, task_id)


@router.post("/spaces/{space_id}/tasks/{task_id}/unclaim", response_model=SpaceTaskRead)
def unclaim_task(space_id: int, task_id: int, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.unclaim(current_user.id, space_id, task_id)


@router.post("/spaces/{space_id}/tasks/{task_id}/assign", response_model=SpaceTaskRead)
def assign_task(space_id: int, task_id: int, payload: SpaceTaskAssignPayload, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.assign(current_user.id, space_id, task_id, payload.assignee_id)


@router.post("/spaces/{space_id}/tasks/{task_id}/complete", response_model=SpaceTaskRead)
def complete_task(space_id: int, task_id: int, payload: SpaceTaskCompletePayload, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.complete(current_user.id, space_id, task_id, payload.is_completed)


@router.post("/spaces/{space_id}/tasks/{task_id}/uncomplete", response_model=SpaceTaskRead)
def uncomplete_task(space_id: int, task_id: int, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.complete(current_user.id, space_id, task_id, False)


@router.post("/spaces/{space_id}/tasks/{task_id}/subtasks", response_model=SpaceSubTaskRead)
def create_subtask(space_id: int, task_id: int, payload: SpaceSubTaskCreate, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.create_subtask(current_user.id, space_id, task_id, payload.title, payload.is_completed)


@router.get("/spaces/{space_id}/tasks/{task_id}/subtasks", response_model=List[SpaceSubTaskRead])
def list_subtasks(space_id: int, task_id: int, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.list_subtasks(current_user.id, space_id, task_id)


@router.patch("/spaces/{space_id}/tasks/{task_id}/subtasks/{subtask_id}", response_model=SpaceSubTaskRead)
def update_subtask(space_id: int, task_id: int, subtask_id: int, payload: SpaceSubTaskUpdate, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.update_subtask(current_user.id, space_id, task_id, subtask_id, title=payload.title, is_completed=payload.is_completed)


@router.delete("/spaces/{space_id}/tasks/{task_id}/subtasks/{subtask_id}", response_model=SpaceSubTaskRead)
def delete_subtask(space_id: int, task_id: int, subtask_id: int, current_user: User = Depends(get_current_user), interactor: SpaceTaskInteractor = Depends(get_space_task_interactor)):
    return interactor.delete_subtask(current_user.id, space_id, task_id, subtask_id)


@router.post("/spaces/{space_id}/notes", response_model=SpaceNoteRead)
def create_note(space_id: int, payload: SpaceNoteCreate, current_user: User = Depends(get_current_user), interactor: SpaceNoteInteractor = Depends(get_space_note_interactor)):
    return interactor.create_note(current_user.id, space_id, payload.title, payload.body)


@router.get("/spaces/{space_id}/notes", response_model=List[SpaceNoteRead])
def list_notes(space_id: int, current_user: User = Depends(get_current_user), interactor: SpaceNoteInteractor = Depends(get_space_note_interactor)):
    return interactor.list_notes(current_user.id, space_id)


@router.get("/spaces/{space_id}/notes/{note_id}", response_model=SpaceNoteRead)
def get_note(space_id: int, note_id: int, current_user: User = Depends(get_current_user), interactor: SpaceNoteInteractor = Depends(get_space_note_interactor)):
    return interactor.get_note(current_user.id, space_id, note_id)


@router.patch("/spaces/{space_id}/notes/{note_id}", response_model=SpaceNoteRead)
def update_note(space_id: int, note_id: int, payload: SpaceNoteUpdate, current_user: User = Depends(get_current_user), interactor: SpaceNoteInteractor = Depends(get_space_note_interactor)):
    return interactor.update_note(current_user.id, space_id, note_id, title=payload.title, body=payload.body)


@router.delete("/spaces/{space_id}/notes/{note_id}", response_model=SpaceNoteRead)
def delete_note(space_id: int, note_id: int, current_user: User = Depends(get_current_user), interactor: SpaceNoteInteractor = Depends(get_space_note_interactor)):
    return interactor.delete_note(current_user.id, space_id, note_id)


@router.post("/shares/notes/{note_id}", response_model=ShareCreatedRead)
def share_note(
    note_id: int,
    payload: ShareCreatePayload,
    current_user: User = Depends(get_current_user),
    space_interactor: SpaceInteractor = Depends(get_space_interactor),
    note_interactor: SpaceNoteInteractor = Depends(get_space_note_interactor),
):
    source_note = None
    source_space_id = None
    for space in space_interactor.list_spaces(current_user.id):
        note = note_interactor.content_repository.get_note(space.id, note_id)
        if note:
            source_note = note
            source_space_id = space.id
            break
    if not source_note or source_space_id is None:
        from app.errors import raise_http

        raise_http(404, "SPACE_NOTE_NOT_FOUND", "Space note not found")

    shared_space = space_interactor.create_space(current_user.id, f"Shared Note {note_id}", "Quick share", is_lightweight=True)
    note_interactor.create_note(current_user.id, shared_space.id, source_note.title, source_note.body)
    for target_user_id in payload.member_user_ids:
        space_interactor.add_member(current_user.id, shared_space.id, target_user_id, payload.role)

    return ShareCreatedRead(space_id=shared_space.id, is_lightweight=shared_space.is_lightweight, shared_entity_type="note", shared_entity_id=note_id)


@router.post("/shares/lists/{list_id}", response_model=ShareCreatedRead)
def share_list(
    list_id: int,
    payload: ShareCreatePayload,
    current_user: User = Depends(get_current_user),
    space_interactor: SpaceInteractor = Depends(get_space_interactor),
    list_interactor: SpaceListInteractor = Depends(get_space_list_interactor),
):
    source_list = None
    for space in space_interactor.list_spaces(current_user.id):
        task_list = list_interactor.content_repository.get_list(space.id, list_id)
        if task_list:
            source_list = task_list
            break
    if not source_list:
        from app.errors import raise_http

        raise_http(404, "SPACE_LIST_NOT_FOUND", "Space list not found")

    shared_space = space_interactor.create_space(current_user.id, f"Shared List {list_id}", "Quick share", is_lightweight=True)
    list_interactor.create_list(current_user.id, shared_space.id, source_list.title, source_list.order)
    for target_user_id in payload.member_user_ids:
        space_interactor.add_member(current_user.id, shared_space.id, target_user_id, payload.role)

    return ShareCreatedRead(space_id=shared_space.id, is_lightweight=shared_space.is_lightweight, shared_entity_type="list", shared_entity_id=list_id)
