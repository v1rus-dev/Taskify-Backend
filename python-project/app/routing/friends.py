from fastapi import APIRouter, Depends, Query
from typing import List
from uuid import UUID

from app.depends import get_friend_service, get_current_user
from app.services.friend_service import FriendService
from app.schemas import FriendRequestCreate, FriendRequestRead, FriendAction, FriendRead
from app.models.user import User


router = APIRouter(prefix="/friends", tags=["Friends"])


@router.put("/tag")
def update_friend_tag(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    new_tag = friend_service.update_friend_tag(current_user.id)
    return {"friend_tag": new_tag}


@router.post("/requests", response_model=FriendRequestRead)
def send_friend_request(
    payload: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    return friend_service.send_request(current_user.id, payload.friend_tag.strip())


@router.get("/requests/incoming", response_model=List[FriendRequestRead])
def list_incoming_requests(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    return friend_service.list_incoming(current_user.id)

@router.get("/requests/outgoing", response_model=List[FriendRequestRead])
def list_outgoing_requests(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    return friend_service.list_outgoing(current_user.id)


@router.post("/requests/accept")
def accept_request(
    payload: FriendAction,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    friend_service.accept_request(current_user.id, payload.requester_id)
    return {"message": "Request accepted"}


@router.post("/requests/decline")
def decline_request(
    payload: FriendAction,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    friend_service.decline_request(current_user.id, payload.requester_id)
    return {"message": "Request declined"}

@router.post("/requests/cancel")
def cancel_request(
    payload: FriendAction,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    friend_service.cancel_request(current_user.id, payload.requester_id)
    return {"message": "Request canceled"}

@router.delete("/{friend_id}")
def remove_friend(
    friend_id: UUID,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    friend_service.remove_friend(current_user.id, friend_id)
    return {"message": "Friend removed"}


@router.get("", response_model=List[FriendRead])
def list_friends(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    return friend_service.list_friends(current_user.id)


@router.get("/resolve")
def resolve_friend_tag(
    friend_tag: str = Query(..., min_length=1, max_length=64),
    friend_service: FriendService = Depends(get_friend_service),
):
    user_id = friend_service.resolve_friend_tag(friend_tag.strip())
    return {"user_id": user_id}
