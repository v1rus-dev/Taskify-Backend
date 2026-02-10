from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID


class SyncEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity: str
    entity_id: int
    op: str
    occurred_at: datetime
    data: Optional[dict[str, Any]] = None


class SyncChangesRead(BaseModel):
    next_cursor: int = Field(..., ge=0)
    changes: List[SyncEventRead]


class SyncOpData(BaseModel):
    # legacy task/subtask/tag fields
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    text: Optional[str] = None
    task_id: Optional[int] = None
    task_client_id: Optional[UUID] = None
    name: Optional[str] = None
    color: Optional[str] = None
    is_user_tag: Optional[bool] = None
    # spaces fields
    space_id: Optional[int] = None
    list_id: Optional[int] = None
    assignee_id: Optional[UUID] = None
    claimed_by_id: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    role: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None
    token: Optional[str] = None
    body: Optional[str] = None
    user_id: Optional[UUID] = None
    is_lightweight: Optional[bool] = None


class SyncOpInput(BaseModel):
    op_id: UUID
    entity: str
    op: str
    id: Optional[int] = None
    client_id: Optional[UUID] = None
    data: Optional[SyncOpData] = None


class SyncPushRequest(BaseModel):
    device_id: Optional[str] = None
    ops: List[SyncOpInput]


class SyncIdMap(BaseModel):
    client_id: UUID
    id: int


class SyncOpError(BaseModel):
    op_id: UUID
    code: str
    message: str


class SyncPushResponse(BaseModel):
    ack: List[UUID] = Field(default_factory=list)
    id_map: Dict[str, List[SyncIdMap]] = Field(default_factory=dict)
    errors: List[SyncOpError] = Field(default_factory=list)
