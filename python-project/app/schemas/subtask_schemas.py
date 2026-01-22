from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SubTaskCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    is_completed: Optional[bool] = False


class SubTaskCreateList(BaseModel):
    subtasks: List[SubTaskCreate]


class SubTaskUpdateItem(BaseModel):
    id: int
    text: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    is_completed: Optional[bool] = None


class SubTaskUpdateList(BaseModel):
    subtasks: List[SubTaskUpdateItem]


class SubTaskUpdate(BaseModel):
    text: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    is_completed: Optional[bool] = None


class SubTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    text: str
    is_completed: bool
    task_id: int
    client_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
