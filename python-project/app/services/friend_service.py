from typing import List
from uuid import UUID
import hashlib
from fastapi import HTTPException, status

from app.repositories.friend_repository import FriendRepository
from app.schemas import FriendRequestRead, FriendRead


class FriendService:
    def __init__(self, friend_repository: FriendRepository):
        self.friend_repository = friend_repository

    def set_friend_tag(self, user_id: UUID, friend_tag: str) -> None:
        user = self.friend_repository.get_user_by_tag(friend_tag)
        if user and user.id != user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User tag already in use")
        current = self.friend_repository.get_user_by_id(user_id)
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        self.friend_repository.set_friend_tag(user_id, friend_tag)

    def update_friend_tag(self, user_id: UUID) -> str:
        current = self.friend_repository.get_user_by_id(user_id)
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return self.friend_repository.set_new_unique_friend_tag(user_id)

    def send_request(self, requester_id: UUID, target_tag: str) -> FriendRequestRead:
        target = self.friend_repository.get_user_by_tag(target_tag)
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        if target.id == requester_id:
            raise HTTPException(status_code=400, detail="Cannot add yourself")
        if self.friend_repository.are_friends(requester_id, target.id):
            raise HTTPException(status_code=409, detail="Already friends")

        existing = self.friend_repository.get_request(requester_id, target.id)
        if existing:
            raise HTTPException(status_code=409, detail="Request already exists")

        reverse = self.friend_repository.get_request(target.id, requester_id)
        if reverse:
            self.friend_repository.delete_request(reverse)
            self.friend_repository.add_friend_pair(requester_id, target.id)
            return FriendRequestRead(
                requester_id=requester_id,
                addressee_id=target.id,
                status="accepted",
            )

        request = self.friend_repository.create_request(requester_id, target.id)
        return FriendRequestRead(
            requester_id=request.requester_id,
            addressee_id=request.addressee_id,
            status=request.status,
        )

    def list_incoming(self, user_id: UUID) -> List[FriendRequestRead]:
        requests = self.friend_repository.list_incoming(user_id)
        return [
            FriendRequestRead(
                requester_id=req.requester_id,
                addressee_id=req.addressee_id,
                status=req.status,
            )
            for req in requests
        ]

    def list_outgoing(self, user_id: UUID) -> List[FriendRequestRead]:
        requests = self.friend_repository.list_outgoing(user_id)
        return [
            FriendRequestRead(
                requester_id=req.requester_id,
                addressee_id=req.addressee_id,
                status=req.status,
            )
            for req in requests
        ]

    def accept_request(self, addressee_id: UUID, requester_id: UUID) -> None:
        request = self.friend_repository.get_request(requester_id, addressee_id)
        if not request or request.status != "pending":
            raise HTTPException(status_code=404, detail="Request not found")
        self.friend_repository.delete_request(request)
        self.friend_repository.add_friend_pair(addressee_id, requester_id)

    def decline_request(self, addressee_id: UUID, requester_id: UUID) -> None:
        request = self.friend_repository.get_request(requester_id, addressee_id)
        if not request or request.status != "pending":
            raise HTTPException(status_code=404, detail="Request not found")
        self.friend_repository.delete_request(request)

    def cancel_request(self, requester_id: UUID, addressee_id: UUID) -> None:
        request = self.friend_repository.get_request(requester_id, addressee_id)
        if not request or request.status != "pending":
            raise HTTPException(status_code=404, detail="Request not found")
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
            raise HTTPException(status_code=404, detail="Friend not found")
        self.friend_repository.remove_friend_pair(user_id, friend_id)

    def resolve_friend_tag(self, friend_tag: str) -> UUID:
        user = self.friend_repository.get_user_by_tag(friend_tag)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user.id

    @staticmethod
    def _anonymous_number(friend_tag: str) -> str:
        digest = hashlib.sha256(friend_tag.encode("utf-8")).digest()
        value = int.from_bytes(digest[:4], "big") % 10000
        return f"{value:04d}"
