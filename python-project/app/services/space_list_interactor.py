from __future__ import annotations

from app.errors import raise_http
from app.repositories.space_content_repository import SpaceContentRepository
from app.services.sync_event_service import SyncEventService
from app.services.space_permission_service import SpacePermissionService, ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR


class SpaceListInteractor:
    def __init__(self, content_repository: SpaceContentRepository, permission_service: SpacePermissionService, sync_event_service: SyncEventService):
        self.content_repository = content_repository
        self.permission_service = permission_service
        self.sync_event_service = sync_event_service

    def create_list(self, user_id, space_id: int, title: str, order: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        row = self.content_repository.create_list(space_id, title, order, user_id)
        self.sync_event_service.log_space_list_event(user_id, row.id, "create")
        return row

    def list_lists(self, user_id, space_id: int):
        self.permission_service.require_member(space_id, user_id)
        return self.content_repository.list_lists(space_id)

    def update_list(self, user_id, space_id: int, list_id: int, title=None, order=None):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        row = self.content_repository.get_list(space_id, list_id)
        if not row:
            raise_http(404, "SPACE_LIST_NOT_FOUND", "Space list not found")
        updated = self.content_repository.update_list(row, title, order, user_id)
        self.sync_event_service.log_space_list_event(user_id, updated.id, "update")
        return updated

    def delete_list(self, user_id, space_id: int, list_id: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        row = self.content_repository.get_list(space_id, list_id)
        if not row:
            raise_http(404, "SPACE_LIST_NOT_FOUND", "Space list not found")
        row_id = row.id
        self.content_repository.delete_list(row)
        self.sync_event_service.log_space_list_event(user_id, row_id, "delete")

    def reorder_lists(self, user_id, space_id: int, items: list[dict]):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        rows = self.content_repository.reorder_lists(space_id, items, user_id)
        for row in rows:
            self.sync_event_service.log_space_list_event(user_id, row.id, "update")
        return rows
