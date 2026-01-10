from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class UserRead(BaseModel):
    id: UUID
    is_anonymous: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
