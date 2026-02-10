from __future__ import annotations

from typing import Iterable
from uuid import UUID

from app.errors import raise_http
from app.repositories.space_repository import SpaceRepository


ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"


class SpacePermissionService:
    def __init__(self, space_repository: SpaceRepository):
        self.space_repository = space_repository

    def require_member(self, space_id: int, user_id: UUID):
        member = self.space_repository.get_member(space_id, user_id)
        if not member or member.status != "active":
            raise_http(403, "INSUFFICIENT_SPACE_ROLE", "User is not an active member")
        return member

    def require_role(self, space_id: int, user_id: UUID, allowed_roles: Iterable[str]):
        member = self.require_member(space_id, user_id)
        if member.role not in set(allowed_roles):
            raise_http(403, "INSUFFICIENT_SPACE_ROLE", "Insufficient space role")
        return member
