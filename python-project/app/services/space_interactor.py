from __future__ import annotations

import secrets
from datetime import datetime, timezone
from uuid import UUID

from app.errors import raise_http
from app.repositories.friend_repository import FriendRepository
from app.repositories.space_repository import SpaceRepository
from app.repositories.space_invite_repository import SpaceInviteRepository
from app.services.space_permission_service import SpacePermissionService, ROLE_OWNER, ROLE_ADMIN
from app.services.sync_event_service import SyncEventService


class SpaceInteractor:
    def __init__(
        self,
        space_repository: SpaceRepository,
        friend_repository: FriendRepository,
        space_invite_repository: SpaceInviteRepository,
        permission_service: SpacePermissionService,
        sync_event_service: SyncEventService,
    ):
        self.space_repository = space_repository
        self.friend_repository = friend_repository
        self.space_invite_repository = space_invite_repository
        self.permission_service = permission_service
        self.sync_event_service = sync_event_service

    def create_space(self, user_id: UUID, name: str, description: str | None, is_lightweight: bool = False):
        space = self.space_repository.create_space(name=name, description=description, created_by=user_id, is_lightweight=is_lightweight)
        self.space_repository.create_member(space.id, user_id, ROLE_OWNER)
        self.sync_event_service.log_space_event(user_id, space.id, "create")
        return space

    def list_spaces(self, user_id: UUID):
        return self.space_repository.list_spaces_for_user(user_id)

    def get_space(self, user_id: UUID, space_id: int):
        self.permission_service.require_member(space_id, user_id)
        space = self.space_repository.get_space(space_id)
        if not space:
            raise_http(404, "SPACE_NOT_FOUND", "Space not found")
        return space

    def delete_space(self, user_id: UUID, space_id: int):
        member = self.permission_service.require_role(space_id, user_id, {ROLE_OWNER})
        if member.role != ROLE_OWNER:
            raise_http(403, "OWNER_ACTION_FORBIDDEN", "Only owner can delete space")
        space = self.space_repository.get_space(space_id)
        if not space:
            raise_http(404, "SPACE_NOT_FOUND", "Space not found")
        space_id_value = space.id
        self.space_repository.delete_space(space)
        self.sync_event_service.log_space_event(user_id, space_id_value, "delete")

    def leave_space(self, user_id: UUID, space_id: int):
        member = self.permission_service.require_member(space_id, user_id)
        if member.role == ROLE_OWNER:
            raise_http(403, "OWNER_ACTION_FORBIDDEN", "Owner cannot leave space")
        self.space_repository.set_member_status(member, "left")
        self.sync_event_service.log_space_member_event(user_id, member.id, "update")

    def list_members(self, user_id: UUID, space_id: int):
        self.permission_service.require_member(space_id, user_id)
        return self.space_repository.list_members(space_id)

    def add_member(self, user_id: UUID, space_id: int, target_user_id: UUID, role: str):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN})
        if role == ROLE_OWNER:
            raise_http(400, "OWNER_TRANSFER_NOT_SUPPORTED", "Owner transfer is not supported")
        if not self.friend_repository.are_friends(user_id, target_user_id):
            raise_http(403, "FORBIDDEN_NOT_FRIEND", "Target user is not your friend")
        member = self.space_repository.activate_or_create_member(space_id, target_user_id, role)
        self.sync_event_service.log_space_member_event(user_id, member.id, "create")
        return member

    def update_member(self, user_id: UUID, space_id: int, target_user_id: UUID, role: str):
        actor = self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN})
        target = self.space_repository.get_member(space_id, target_user_id)
        if not target or target.status != "active":
            raise_http(404, "SPACE_MEMBER_NOT_FOUND", "Space member not found")
        if role == ROLE_OWNER:
            raise_http(400, "OWNER_TRANSFER_NOT_SUPPORTED", "Owner transfer is not supported")
        if actor.role == ROLE_ADMIN and target.role == ROLE_OWNER:
            raise_http(403, "OWNER_ACTION_FORBIDDEN", "Admin cannot edit owner role")
        if target.role == ROLE_OWNER:
            raise_http(403, "OWNER_ACTION_FORBIDDEN", "Owner role cannot be changed")
        member = self.space_repository.update_member_role(target, role)
        self.sync_event_service.log_space_member_event(user_id, member.id, "update")
        return member

    def remove_member(self, user_id: UUID, space_id: int, target_user_id: UUID):
        actor = self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN})
        target = self.space_repository.get_member(space_id, target_user_id)
        if not target or target.status != "active":
            raise_http(404, "SPACE_MEMBER_NOT_FOUND", "Space member not found")
        if actor.role == ROLE_ADMIN and target.role == ROLE_OWNER:
            raise_http(403, "OWNER_ACTION_FORBIDDEN", "Admin cannot remove owner")
        if target.role == ROLE_OWNER:
            raise_http(403, "OWNER_ACTION_FORBIDDEN", "Owner cannot be removed")
        member = self.space_repository.set_member_status(target, "removed")
        self.sync_event_service.log_space_member_event(user_id, member.id, "delete")
        return member

    def create_invite(self, user_id: UUID, space_id: int, role: str, expires_at: datetime):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN})
        if role == ROLE_OWNER:
            raise_http(400, "OWNER_TRANSFER_NOT_SUPPORTED", "Owner transfer is not supported")
        token = secrets.token_urlsafe(24)
        invite = self.space_invite_repository.create_invite(space_id=space_id, inviter_id=user_id, role=role, token=token, expires_at=expires_at)
        self.sync_event_service.log_space_invite_event(user_id, invite.id, "create")
        return invite

    def list_invites(self, user_id: UUID, space_id: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN})
        return self.space_invite_repository.list_invites(space_id)

    def accept_invite(self, user_id: UUID, token: str):
        invite = self.space_invite_repository.get_by_token(token)
        if not invite:
            raise_http(404, "SPACE_INVITE_NOT_FOUND", "Space invite not found")
        if invite.status != "active":
            raise_http(409, "SPACE_INVITE_REVOKED", "Space invite is revoked")
        if invite.expires_at < datetime.now(timezone.utc):
            raise_http(409, "SPACE_INVITE_EXPIRED", "Space invite is expired")
        member = self.space_repository.activate_or_create_member(invite.space_id, user_id, invite.role)
        self.sync_event_service.log_space_member_event(user_id, member.id, "create")
        return invite.space_id, member

    def revoke_invite(self, user_id: UUID, space_id: int, invite_id: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN})
        invite = self.space_invite_repository.get_invite(invite_id)
        if not invite or invite.space_id != space_id:
            raise_http(404, "SPACE_INVITE_NOT_FOUND", "Space invite not found")
        revoked = self.space_invite_repository.revoke(invite)
        self.sync_event_service.log_space_invite_event(user_id, revoked.id, "delete")
        return revoked

    def expand_space(self, user_id: UUID, space_id: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN})
        space = self.space_repository.get_space(space_id)
        if not space:
            raise_http(404, "SPACE_NOT_FOUND", "Space not found")
        space.is_lightweight = False
        self.space_repository.db.commit()
        self.space_repository.db.refresh(space)
        self.sync_event_service.log_space_event(user_id, space.id, "update")
        return space
