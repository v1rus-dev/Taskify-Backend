from pydantic import BaseModel, Field, ConfigDict
from typing import List
from uuid import UUID


class FriendRequestCreate(BaseModel):
    friend_tag: str = Field(..., min_length=1, max_length=64)

class FriendRequestRead(BaseModel):
    requester_id: UUID
    addressee_id: UUID


class FriendRequestUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: str | None = None
    image_url: str | None = Field(default=None, alias="imageUrl")
    display_name: str = Field(..., alias="displayName")


class FriendRequestListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: UUID = Field(..., alias="requestId")
    user: FriendRequestUser


class FriendAction(BaseModel):
    request_id: UUID = Field(..., alias="requestId")


class FriendRead(BaseModel):
    id: UUID
    friend_tag: str
    name: str | None = None
    avatar_url: str | None = None
    anonymous_number: str | None = None


class FriendsList(BaseModel):
    friends: List[FriendRead]
