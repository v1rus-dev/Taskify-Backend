from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID

from app.depends import get_current_user, get_space_interactor
from app.models.user import User
from app.schemas import (
    SpaceCreate,
    SpaceRead,
    SpaceMemberCreate,
    SpaceMemberUpdate,
    SpaceMemberRead,
    SpaceInviteCreate,
    SpaceInviteRead,
    SpaceInviteAcceptRead,
)
from app.services.space_interactor import SpaceInteractor


router = APIRouter(prefix="/spaces", tags=["Spaces"])


@router.post("", response_model=SpaceRead)
def create_space(
    payload: SpaceCreate,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.create_space(current_user.id, payload.name, payload.description, payload.is_lightweight)


@router.get("", response_model=List[SpaceRead])
def list_spaces(
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.list_spaces(current_user.id)


@router.get("/{space_id}", response_model=SpaceRead)
def get_space(
    space_id: int,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.get_space(current_user.id, space_id)


@router.post("/{space_id}/leave")
def leave_space(
    space_id: int,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    interactor.leave_space(current_user.id, space_id)
    return {"status": "left"}


@router.delete("/{space_id}", status_code=204)
def delete_space(
    space_id: int,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    interactor.delete_space(current_user.id, space_id)


@router.get("/{space_id}/members", response_model=List[SpaceMemberRead])
def list_members(
    space_id: int,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.list_members(current_user.id, space_id)


@router.post("/{space_id}/members", response_model=SpaceMemberRead)
def add_member(
    space_id: int,
    payload: SpaceMemberCreate,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.add_member(current_user.id, space_id, payload.user_id, payload.role)


@router.patch("/{space_id}/members/{user_id}", response_model=SpaceMemberRead)
def update_member(
    space_id: int,
    user_id: UUID,
    payload: SpaceMemberUpdate,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.update_member(current_user.id, space_id, user_id, payload.role)


@router.delete("/{space_id}/members/{user_id}", status_code=204)
def remove_member(
    space_id: int,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    interactor.remove_member(current_user.id, space_id, user_id)


@router.post("/{space_id}/invites", response_model=SpaceInviteRead)
def create_invite(
    space_id: int,
    payload: SpaceInviteCreate,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.create_invite(current_user.id, space_id, payload.role, payload.expires_at)


@router.get("/{space_id}/invites", response_model=List[SpaceInviteRead])
def list_invites(
    space_id: int,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.list_invites(current_user.id, space_id)


@router.post("/invites/{token}/accept", response_model=SpaceInviteAcceptRead)
def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    space_id, member = interactor.accept_invite(current_user.id, token)
    return SpaceInviteAcceptRead(space_id=space_id, member=SpaceMemberRead.model_validate(member))


@router.post("/{space_id}/invites/{invite_id}/revoke", response_model=SpaceInviteRead)
def revoke_invite(
    space_id: int,
    invite_id: int,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.revoke_invite(current_user.id, space_id, invite_id)


@router.post("/{space_id}/expand", response_model=SpaceRead)
def expand_space(
    space_id: int,
    current_user: User = Depends(get_current_user),
    interactor: SpaceInteractor = Depends(get_space_interactor),
):
    return interactor.expand_space(current_user.id, space_id)
