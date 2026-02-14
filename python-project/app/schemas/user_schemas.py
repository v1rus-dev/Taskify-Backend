from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    provider: str
    provider_user_id: str
    email: Optional[str]
    name: Optional[str]
    avatar_url: Optional[str]
    friend_tag: str
    created_at: datetime
    updated_at: datetime
