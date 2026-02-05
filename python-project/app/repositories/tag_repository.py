from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.tag import Tag
from app.models.task_tag import task_tags


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID, tag_id: int, include_deleted: bool = False) -> Optional[Tag]:
        query = self.db.query(Tag).filter(Tag.user_id == user_id, Tag.id == tag_id)
        if not include_deleted:
            query = query.filter(Tag.deleted_at.is_(None))
        return query.first()

    def get_by_identity(self, user_id: UUID, is_user_tag: bool, name: str, color: str) -> Optional[Tag]:
        return (
            self.db.query(Tag)
            .filter(
                Tag.user_id == user_id,
                Tag.is_user_tag == is_user_tag,
                Tag.name == name,
                Tag.color == color,
                Tag.deleted_at.is_(None),
            )
            .first()
        )

    def get_user_tags(self, user_id: UUID, include_deleted: bool = False) -> List[Tag]:
        query = (
            self.db.query(Tag)
            .filter(
                Tag.user_id == user_id,
                Tag.is_user_tag.is_(True),
            )
        )
        if not include_deleted:
            query = query.filter(Tag.deleted_at.is_(None))
        return query.order_by(Tag.name.asc()).all()

    def _next_tag_id(self, user_id: UUID) -> int:
        stmt = select(func.coalesce(func.max(Tag.id), 0)).where(Tag.user_id == user_id)
        current = self.db.execute(stmt).scalar() or 0
        return int(current) + 1

    def create(
        self,
        user_id: UUID,
        is_user_tag: bool,
        name: str,
        color: str,
        tag_id: Optional[int] = None,
        client_id: Optional[UUID] = None,
    ) -> Tag:
        resolved_id = tag_id if tag_id is not None else self._next_tag_id(user_id)
        tag = Tag(
            id=resolved_id,
            user_id=user_id,
            is_user_tag=is_user_tag,
            name=name,
            color=color,
            client_id=client_id,
        )
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def update(self, tag: Tag, is_user_tag: bool, name: str, color: str) -> Tag:
        tag.is_user_tag = is_user_tag
        tag.name = name
        tag.color = color
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def delete(self, tag: Tag) -> Tag:
        tag.deleted_at = func.now()
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def is_tag_linked(self, user_id: UUID, tag_id: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(task_tags)
            .where(
                task_tags.c.tag_id == tag_id,
                task_tags.c.tag_user_id == user_id,
            )
        )
        count = self.db.execute(stmt).scalar() or 0
        return count > 0

    def commit(self) -> None:
        self.db.commit()

    def get_by_client_id(self, user_id: UUID, client_id: UUID, include_deleted: bool = True) -> Optional[Tag]:
        query = self.db.query(Tag).filter(Tag.user_id == user_id, Tag.client_id == client_id)
        if not include_deleted:
            query = query.filter(Tag.deleted_at.is_(None))
        return query.first()
