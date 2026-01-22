from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class TagBase(BaseModel):
    is_user_tag: bool = True
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    color: Optional[str] = Field(default=None, min_length=1, max_length=32)


class TagInput(TagBase):
    id: Optional[int] = None


class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
