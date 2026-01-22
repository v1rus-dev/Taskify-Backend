from typing import List
from uuid import UUID

from app.repositories.tag_repository import TagRepository
from app.schemas import TagRead


class TagService:
    def __init__(self, tag_repository: TagRepository):
        self.tag_repository = tag_repository

    def get_user_tags(self, user_id: UUID) -> List[TagRead]:
        tags = self.tag_repository.get_user_tags(user_id)
        return [TagRead.model_validate(tag) for tag in tags]
