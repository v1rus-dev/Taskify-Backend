from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class SubTaskCreate(BaseModel):
    text: str
    is_completed: Optional[bool] = False


class SubTaskCreateList(BaseModel):
    subtasks: List[SubTaskCreate]


class SubTaskUpdateItem(BaseModel):
    id: int
    text: Optional[str] = None
    is_completed: Optional[bool] = None


class SubTaskUpdateList(BaseModel):
    subtasks: List[SubTaskUpdateItem]


class SubTaskUpdate(BaseModel):
    text: Optional[str] = None
    is_completed: Optional[bool] = None


class SubTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    text: str
    is_completed: bool
    task_id: int
    created_at: datetime
    updated_at: datetime
