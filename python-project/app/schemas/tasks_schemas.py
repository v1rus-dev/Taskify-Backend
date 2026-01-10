from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_completed: Optional[bool] = None

class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_completed: bool
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True