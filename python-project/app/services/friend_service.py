from typing import List
from uuid import UUID
import hashlib
from app.errors import raise_http

from app.repositories.friend_repository import FriendRepository
from app.schemas import FriendRequestListItem, FriendRequestUser, FriendRead


class FriendService:
    def __init__(self, friend_repository: FriendRepository):
        self.friend_repository = friend_repository

    def set_friend_tag(self, user_id: UUID, friend_tag: str) -> None:
        user = self.friend_repository.get_user_by_tag(friend_tag)
        if user and user.id != user_id:
            raise_http(409, "FRIEND_TAG_IN_USE", "User tag already in use")
        current = self.friend_repository.get_user_by_id(user_id)
        if not current:
            raise_http(404, "USER_NOT_FOUND", "User not found")
        self.friend_repository.set_friend_tag(user_id, friend_tag)

    def update_friend_tag(self, user_id: UUID) -> str:
        current = self.friend_repository.get_user_by_id(user_id)
        if not current:
            raise_http(404, "USER_NOT_FOUND", "User not found")
        return self.friend_repository.set_new_unique_friend_tag(user_id)

    def send_request(self, requester_id: UUID, target_tag: str) -> FriendRequestListItem:
        target = self.friend_repository.get_user_by_tag(target_tag)
        if not target:
            raise_http(404, "USER_NOT_FOUND", "User not found")
        if target.id == requester_id:
            raise_http(400, "CANNOT_ADD_SELF", "Cannot add yourself")
        if self.friend_repository.are_friends(requester_id, target.id):
            raise_http(409, "ALREADY_FRIENDS", "Already friends")

        existing = self.friend_repository.get_request(requester_id, target.id)
        if existing:
            raise_http(409, "REQUEST_ALREADY_EXISTS", "Request already exists")

        reverse = self.friend_repository.get_request(target.id, requester_id)
        if reverse:
            self.friend_repository.delete_request(reverse)
            self.friend_repository.add_friend_pair(requester_id, target.id)
            raise_http(
                410,
                "AUTO_ACCEPTED",
                "Auto-accepted friend request",
                details={"userId": str(target.id)},
            )

        request = self.friend_repository.create_request(requester_id, target.id)
        return FriendRequestListItem(
            request_id=request.id,
            user=self._build_request_user(target),
        )

    def list_incoming(self, user_id: UUID) -> List[FriendRequestListItem]:
        rows = self.friend_repository.list_incoming_with_users(user_id)
        return [
            FriendRequestListItem(
                request_id=req.id,
                user=self._build_request_user(user),
            )
            for req, user in rows
        ]

    def list_outgoing(self, user_id: UUID) -> List[FriendRequestListItem]:
        rows = self.friend_repository.list_outgoing_with_users(user_id)
        return [
            FriendRequestListItem(
                request_id=req.id,
                user=self._build_request_user(user),
            )
            for req, user in rows
        ]

    def accept_request(self, addressee_id: UUID, request_id: UUID) -> FriendRead:
        request = self.friend_repository.get_request_by_id(request_id)
        if not request or request.addressee_id != addressee_id:
            raise_http(404, "REQUEST_NOT_FOUND", "Request not found")
        self.friend_repository.delete_request(request)
        self.friend_repository.add_friend_pair(addressee_id, request.requester_id)
        friend = self.friend_repository.get_user_by_id(request.requester_id)
        if not friend:
            raise_http(404, "USER_NOT_FOUND", "User not found")
        return FriendRead(
            id=friend.id,
            friend_tag=friend.friend_tag,
            name=friend.name,
            avatar_url=friend.avatar_url,
            anonymous_number=self._anonymous_number(friend.friend_tag),
        )

    def decline_request(self, addressee_id: UUID, request_id: UUID) -> None:
        request = self.friend_repository.get_request_by_id(request_id)
        if not request or request.addressee_id != addressee_id:
            raise_http(404, "REQUEST_NOT_FOUND", "Request not found")
        self.friend_repository.delete_request(request)

    def cancel_request(self, requester_id: UUID, request_id: UUID) -> None:
        request = self.friend_repository.get_request_by_id(request_id)
        if not request or request.requester_id != requester_id:
            raise_http(404, "REQUEST_NOT_FOUND", "Request not found")
        self.friend_repository.delete_request(request)

    def list_friends(self, user_id: UUID) -> List[FriendRead]:
        friends = self.friend_repository.list_friends(user_id)
        return [
            FriendRead(
                id=user.id,
                friend_tag=user.friend_tag,
                name=user.name,
                avatar_url=user.avatar_url,
                anonymous_number=self._anonymous_number(user.friend_tag),
            )
            for user in friends
        ]

    def remove_friend(self, user_id: UUID, friend_id: UUID) -> None:
        if not self.friend_repository.are_friends(user_id, friend_id):
            raise_http(404, "FRIEND_NOT_FOUND", "Friend not found")
        self.friend_repository.remove_friend_pair(user_id, friend_id)

    @staticmethod
    def _anonymous_number(friend_tag: str) -> str:
        digest = hashlib.sha256(friend_tag.encode("utf-8")).digest()
        value = int.from_bytes(digest[:4], "big") % 10000
        return f"{value:04d}"

    def _build_request_user(self, user) -> FriendRequestUser:
        display_name = user.name or f"Anonymous {self._anonymous_number(user.friend_tag)}"
        return FriendRequestUser(
            id=user.id,
            name=user.name,
            image_url=user.avatar_url,
            display_name=display_name,
        )
