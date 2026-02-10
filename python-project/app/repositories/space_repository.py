from __future__ import annotations

from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.space import Space
from app.models.space_member import SpaceMember


class SpaceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_space(self, name: str, description: Optional[str], created_by: UUID, is_lightweight: bool = False, client_id=None) -> Space:
        space = Space(
            name=name,
            description=description,
            created_by=created_by,
            is_lightweight=is_lightweight,
            client_id=client_id,
        )
        self.db.add(space)
        self.db.commit()
        self.db.refresh(space)
        return space

    def get_space(self, space_id: int) -> Optional[Space]:
        return self.db.query(Space).filter(Space.id == space_id).first()

    def get_space_by_client_id(self, client_id) -> Optional[Space]:
        return self.db.query(Space).filter(Space.client_id == client_id).first()

    def list_spaces_for_user(self, user_id: UUID) -> List[Space]:
        return (
            self.db.query(Space)
            .join(SpaceMember, SpaceMember.space_id == Space.id)
            .filter(SpaceMember.user_id == user_id, SpaceMember.status == "active")
            .order_by(Space.updated_at.desc())
            .all()
        )

    def delete_space(self, space: Space) -> None:
        self.db.delete(space)
        self.db.commit()

    def create_member(self, space_id: int, user_id: UUID, role: str, status: str = "active") -> SpaceMember:
        member = SpaceMember(space_id=space_id, user_id=user_id, role=role, status=status)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_member(self, space_id: int, user_id: UUID) -> Optional[SpaceMember]:
        return (
            self.db.query(SpaceMember)
            .filter(SpaceMember.space_id == space_id, SpaceMember.user_id == user_id)
            .first()
        )

    def get_member_by_id(self, member_id: int) -> Optional[SpaceMember]:
        return self.db.query(SpaceMember).filter(SpaceMember.id == member_id).first()

    def list_members(self, space_id: int) -> List[SpaceMember]:
        return (
            self.db.query(SpaceMember)
            .filter(SpaceMember.space_id == space_id, SpaceMember.status == "active")
            .order_by(SpaceMember.joined_at.asc())
            .all()
        )

    def update_member_role(self, member: SpaceMember, role: str) -> SpaceMember:
        member.role = role
        self.db.commit()
        self.db.refresh(member)
        return member

    def set_member_status(self, member: SpaceMember, status: str) -> SpaceMember:
        member.status = status
        self.db.commit()
        self.db.refresh(member)
        return member

    def activate_or_create_member(self, space_id: int, user_id: UUID, role: str) -> SpaceMember:
        member = self.get_member(space_id, user_id)
        if member:
            member.status = "active"
            member.role = role
            self.db.commit()
            self.db.refresh(member)
            return member
        return self.create_member(space_id, user_id, role, status="active")
