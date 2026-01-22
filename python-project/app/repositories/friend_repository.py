from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.friend import FriendRequest
from app.models.user_friend import user_friends


class FriendRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_tag(self, friend_tag: str) -> Optional[User]:
        return self.db.query(User).filter(User.friend_tag == friend_tag).first()

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def set_friend_tag(self, user_id: UUID, friend_tag: str) -> None:
        user = self.get_user_by_id(user_id)
        if not user:
            return
        user.friend_tag = friend_tag
        self.db.commit()

    def get_request(self, requester_id: UUID, addressee_id: UUID) -> Optional[FriendRequest]:
        return (
            self.db.query(FriendRequest)
            .filter(
                FriendRequest.requester_id == requester_id,
                FriendRequest.addressee_id == addressee_id,
            )
            .first()
        )

    def create_request(self, requester_id: UUID, addressee_id: UUID) -> FriendRequest:
        request = FriendRequest(
            requester_id=requester_id,
            addressee_id=addressee_id,
            status="pending",
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def delete_request(self, request: FriendRequest) -> None:
        self.db.delete(request)
        self.db.commit()

    def list_incoming(self, user_id: UUID) -> List[FriendRequest]:
        return (
            self.db.query(FriendRequest)
            .filter(FriendRequest.addressee_id == user_id, FriendRequest.status == "pending")
            .order_by(FriendRequest.created_at.desc())
            .all()
        )

    def list_outgoing(self, user_id: UUID) -> List[FriendRequest]:
        return (
            self.db.query(FriendRequest)
            .filter(FriendRequest.requester_id == user_id, FriendRequest.status == "pending")
            .order_by(FriendRequest.created_at.desc())
            .all()
        )

    def get_request_by_requester(self, requester_id: UUID, addressee_id: UUID) -> Optional[FriendRequest]:
        return (
            self.db.query(FriendRequest)
            .filter(
                FriendRequest.requester_id == requester_id,
                FriendRequest.addressee_id == addressee_id,
            )
            .first()
        )

    def list_friends(self, user_id: UUID) -> List[User]:
        return (
            self.db.query(User)
            .join(user_friends, User.id == user_friends.c.friend_id)
            .filter(user_friends.c.user_id == user_id)
            .all()
        )

    def are_friends(self, user_id: UUID, friend_id: UUID) -> bool:
        result = self.db.execute(
            user_friends.select().where(
                and_(user_friends.c.user_id == user_id, user_friends.c.friend_id == friend_id)
            )
        ).first()
        return result is not None

    def add_friend_pair(self, user_id: UUID, friend_id: UUID) -> None:
        self.db.execute(
            user_friends.insert().values(user_id=user_id, friend_id=friend_id)
        )
        self.db.execute(
            user_friends.insert().values(user_id=friend_id, friend_id=user_id)
        )
        self.db.commit()

    def remove_friend_pair(self, user_id: UUID, friend_id: UUID) -> None:
        self.db.execute(
            user_friends.delete().where(
                and_(user_friends.c.user_id == user_id, user_friends.c.friend_id == friend_id)
            )
        )
        self.db.execute(
            user_friends.delete().where(
                and_(user_friends.c.user_id == friend_id, user_friends.c.friend_id == user_id)
            )
        )
        self.db.commit()
