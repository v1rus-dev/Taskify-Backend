from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID

from app.depends import get_friend_service, get_current_user
from app.services.friend_service import FriendService
from app.schemas import FriendRequestCreate, FriendRequestListItem, FriendAction, FriendRead
from app.models.user import User
from app.routing.docs import error_response


router = APIRouter(prefix="/friends", tags=["Friends"])


@router.put(
    "/tag",
    summary="Regenerate friend tag",
    description="Generates a new unique friend tag for the current user.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("USER_NOT_FOUND", "User not found", "User not found."),
    },
)
def update_friend_tag(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    new_tag = friend_service.update_friend_tag(current_user.id)
    return {"friend_tag": new_tag}


@router.post(
    "/requests",
    response_model=FriendRequestListItem,
    summary="Send friend request",
    description="Sends a friend request by friend tag.",
    responses={
        400: error_response("CANNOT_ADD_SELF", "Cannot add yourself", "Cannot send request to yourself."),
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("USER_NOT_FOUND", "User not found", "Target user not found."),
        409: error_response(
            "ALREADY_FRIENDS",
            "Already friends",
            "Conflict. Possible codes: ALREADY_FRIENDS, REQUEST_ALREADY_EXISTS.",
        ),
        410: error_response("AUTO_ACCEPTED", "Auto-accepted friend request", "Incoming request auto-accepted.", details={"user_id": "00000000-0000-0000-0000-000000000000"}),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def send_friend_request(
    payload: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    return friend_service.send_request(current_user.id, payload.friend_tag.strip())


@router.get(
    "/requests/incoming",
    response_model=List[FriendRequestListItem],
    summary="List incoming requests",
    description="Returns incoming friend requests for the current user.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
    },
)
def list_incoming_requests(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    return friend_service.list_incoming(current_user.id)

@router.get(
    "/requests/outgoing",
    response_model=List[FriendRequestListItem],
    summary="List outgoing requests",
    description="Returns outgoing friend requests for the current user.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
    },
)
def list_outgoing_requests(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    return friend_service.list_outgoing(current_user.id)


@router.post(
    "/requests/accept",
    response_model=FriendRead,
    summary="Accept friend request",
    description="Accepts an incoming friend request by request_id.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("REQUEST_NOT_FOUND", "Request not found", "Request not found."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def accept_request(
    payload: FriendAction,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    return friend_service.accept_request(current_user.id, payload.request_id)


@router.post(
    "/requests/decline",
    summary="Decline friend request",
    description="Declines an incoming friend request by request_id.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("REQUEST_NOT_FOUND", "Request not found", "Request not found."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def decline_request(
    payload: FriendAction,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    friend_service.decline_request(current_user.id, payload.request_id)
    return {"message": "Request declined"}

@router.post(
    "/requests/cancel",
    summary="Cancel outgoing request",
    description="Cancels an outgoing friend request by request_id.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("REQUEST_NOT_FOUND", "Request not found", "Request not found."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def cancel_request(
    payload: FriendAction,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    friend_service.cancel_request(current_user.id, payload.request_id)
    return {"message": "Request canceled"}

@router.delete(
    "/{friend_id}",
    summary="Remove friend",
    description="Removes a friend by user ID.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        404: error_response("FRIEND_NOT_FOUND", "Friend not found", "Friend not found."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid friend ID."),
    },
)
def remove_friend(
    friend_id: UUID,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    friend_service.remove_friend(current_user.id, friend_id)
    return {"message": "Friend removed"}


@router.get(
    "",
    response_model=List[FriendRead],
    summary="List friends",
    description="Returns the current user's friends.",
    responses={
        401: error_response("AUTH_HEADER_MISSING_OR_INVALID", "Authorization header missing or invalid", "Missing or invalid auth."),
    },
)
def list_friends(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    return friend_service.list_friends(current_user.id)
