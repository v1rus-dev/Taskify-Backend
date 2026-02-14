from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


class FriendRequestCreate(BaseModel):
    friend_tag: str = Field(..., min_length=1, max_length=64)

class FriendRequestRead(BaseModel):
    requester_id: UUID
    addressee_id: UUID


class FriendRead(BaseModel):
    id: UUID
    friend_tag: str
    name: str | None = None
    avatar_url: str | None = None
    anonymous_number: str | None = None


class FriendRequestListItem(BaseModel):
    request_id: UUID
    user: FriendRead


class FriendAction(BaseModel):
    request_id: UUID


class FriendsList(BaseModel):
    friends: List[FriendRead]


class FriendStatusRead(BaseModel):
    is_friend: bool
    user: FriendRead
