from __future__ import annotations

from app.errors import raise_http
from app.repositories.space_content_repository import SpaceContentRepository
from app.services.sync_event_service import SyncEventService
from app.services.space_permission_service import SpacePermissionService, ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR


class SpaceNoteInteractor:
    def __init__(self, content_repository: SpaceContentRepository, permission_service: SpacePermissionService, sync_event_service: SyncEventService):
        self.content_repository = content_repository
        self.permission_service = permission_service
        self.sync_event_service = sync_event_service

    def create_note(self, user_id, space_id: int, title: str, body: str):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        row = self.content_repository.create_note(space_id, title, body, user_id)
        self.sync_event_service.log_space_note_event(user_id, row.id, "create")
        return row

    def list_notes(self, user_id, space_id: int):
        self.permission_service.require_member(space_id, user_id)
        return self.content_repository.list_notes(space_id)

    def get_note(self, user_id, space_id: int, note_id: int):
        self.permission_service.require_member(space_id, user_id)
        note = self.content_repository.get_note(space_id, note_id)
        if not note:
            raise_http(404, "SPACE_NOTE_NOT_FOUND", "Space note not found")
        return note

    def update_note(self, user_id, space_id: int, note_id: int, title=None, body=None):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        note = self.content_repository.get_note(space_id, note_id)
        if not note:
            raise_http(404, "SPACE_NOTE_NOT_FOUND", "Space note not found")
        updated = self.content_repository.update_note(note, user_id, title=title, body=body)
        self.sync_event_service.log_space_note_event(user_id, updated.id, "update")
        return updated

    def delete_note(self, user_id, space_id: int, note_id: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        note = self.content_repository.get_note(space_id, note_id)
        if not note:
            raise_http(404, "SPACE_NOTE_NOT_FOUND", "Space note not found")
        deleted = self.content_repository.delete_note(note, user_id)
        self.sync_event_service.log_space_note_event(user_id, deleted.id, "delete")
        return deleted
