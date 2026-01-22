from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .tag_schemas import TagInput, TagRead

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    is_completed: Optional[bool] = None
    tags: List[TagInput] = Field(default_factory=list)

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    is_completed: Optional[bool] = None
    tags: Optional[List[TagInput]] = None

class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str] = None
    is_completed: bool
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    tags: List[TagRead] = Field(default_factory=list)
