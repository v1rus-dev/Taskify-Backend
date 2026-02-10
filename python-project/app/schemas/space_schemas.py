from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SpaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    is_lightweight: bool = False


class SpaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    is_lightweight: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class SpaceMemberCreate(BaseModel):
    user_id: UUID
    role: str = Field(..., pattern="^(admin|editor|viewer)$")


class SpaceMemberUpdate(BaseModel):
    role: str = Field(..., pattern="^(admin|editor|viewer)$")


class SpaceMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    user_id: UUID
    role: str
    status: str
    joined_at: datetime


class SpaceInviteCreate(BaseModel):
    role: str = Field(..., pattern="^(admin|editor|viewer)$")
    expires_at: datetime


class SpaceInviteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    inviter_id: UUID
    role: str
    token: str
    expires_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime


class SpaceInviteAcceptRead(BaseModel):
    space_id: int
    member: SpaceMemberRead


class SpaceListCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    order: int = 0


class SpaceListUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    order: Optional[int] = None


class SpaceListReorderItem(BaseModel):
    id: int
    order: int


class SpaceListReorderPayload(BaseModel):
    items: List[SpaceListReorderItem]


class SpaceListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    title: str
    order: int
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime


class SpaceTaskCreate(BaseModel):
    list_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    assignee_id: Optional[UUID] = None


class SpaceTaskUpdate(BaseModel):
    list_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    assignee_id: Optional[UUID] = None


class SpaceTaskAssignPayload(BaseModel):
    assignee_id: Optional[UUID] = None


class SpaceTaskCompletePayload(BaseModel):
    is_completed: bool


class SpaceTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    list_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    assignee_id: Optional[UUID] = None
    claimed_by_id: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime


class SpaceSubTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    is_completed: bool = False


class SpaceSubTaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_completed: Optional[bool] = None


class SpaceSubTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    title: str
    is_completed: bool
    deleted_at: Optional[datetime] = None
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime


class SpaceNoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1, max_length=20000)


class SpaceNoteUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, min_length=1, max_length=20000)


class SpaceNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    title: str
    body: str
    deleted_at: Optional[datetime] = None
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime


class ShareCreatePayload(BaseModel):
    member_user_ids: List[UUID] = Field(default_factory=list)
    role: str = Field(default="viewer", pattern="^(admin|editor|viewer)$")


class ShareCreatedRead(BaseModel):
    space_id: int
    is_lightweight: bool
    shared_entity_type: str
    shared_entity_id: int
