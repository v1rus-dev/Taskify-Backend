from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True