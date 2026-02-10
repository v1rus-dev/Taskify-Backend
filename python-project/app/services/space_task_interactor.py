from __future__ import annotations

from app.errors import raise_http
from app.repositories.space_content_repository import SpaceContentRepository
from app.repositories.space_repository import SpaceRepository
from app.services.sync_event_service import SyncEventService
from app.services.space_permission_service import SpacePermissionService, ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER


class SpaceTaskInteractor:
    def __init__(
        self,
        content_repository: SpaceContentRepository,
        space_repository: SpaceRepository,
        permission_service: SpacePermissionService,
        sync_event_service: SyncEventService,
    ):
        self.content_repository = content_repository
        self.space_repository = space_repository
        self.permission_service = permission_service
        self.sync_event_service = sync_event_service

    def create_task(self, user_id, space_id: int, list_id, title: str, description, assignee_id):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        if assignee_id and not self.space_repository.get_member(space_id, assignee_id):
            raise_http(400, "ASSIGNEE_NOT_SPACE_MEMBER", "Assignee must be a space member")
        row = self.content_repository.create_task(space_id, list_id, title, description, assignee_id, user_id)
        self.sync_event_service.log_space_task_event(user_id, row.id, "create")
        return row

    def list_tasks(self, user_id, space_id: int, list_id=None, assignee_id=None, include_completed=True):
        self.permission_service.require_member(space_id, user_id)
        return self.content_repository.list_tasks(space_id, list_id=list_id, assignee_id=assignee_id, include_completed=include_completed)

    def get_task(self, user_id, space_id: int, task_id: int):
        self.permission_service.require_member(space_id, user_id)
        task = self.content_repository.get_task(space_id, task_id)
        if not task:
            raise_http(404, "SPACE_TASK_NOT_FOUND", "Space task not found")
        return task

    def update_task(self, user_id, space_id: int, task_id: int, **kwargs):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        task = self.content_repository.get_task(space_id, task_id)
        if not task:
            raise_http(404, "SPACE_TASK_NOT_FOUND", "Space task not found")
        assignee_id = kwargs.get("assignee_id")
        if assignee_id and not self.space_repository.get_member(space_id, assignee_id):
            raise_http(400, "ASSIGNEE_NOT_SPACE_MEMBER", "Assignee must be a space member")
        updated = self.content_repository.update_task(task, user_id, **kwargs)
        self.sync_event_service.log_space_task_event(user_id, updated.id, "update")
        return updated

    def delete_task(self, user_id, space_id: int, task_id: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        task = self.content_repository.get_task(space_id, task_id)
        if not task:
            raise_http(404, "SPACE_TASK_NOT_FOUND", "Space task not found")
        deleted = self.content_repository.delete_task(task, user_id)
        self.sync_event_service.log_space_task_event(user_id, deleted.id, "delete")
        return deleted

    def claim(self, user_id, space_id: int, task_id: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        task = self.get_task(user_id, space_id, task_id)
        updated = self.content_repository.update_task(task, user_id, claimed_by_id=user_id, assignee_id=user_id)
        self.sync_event_service.log_space_task_event(user_id, updated.id, "update")
        return updated

    def unclaim(self, user_id, space_id: int, task_id: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        task = self.get_task(user_id, space_id, task_id)
        task.claimed_by_id = None
        task.updated_by = user_id
        self.content_repository.db.commit()
        self.content_repository.db.refresh(task)
        self.sync_event_service.log_space_task_event(user_id, task.id, "update")
        return task

    def assign(self, user_id, space_id: int, task_id: int, assignee_id):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        task = self.get_task(user_id, space_id, task_id)
        if assignee_id and not self.space_repository.get_member(space_id, assignee_id):
            raise_http(400, "ASSIGNEE_NOT_SPACE_MEMBER", "Assignee must be a space member")
        updated = self.content_repository.update_task(task, user_id, assignee_id=assignee_id)
        self.sync_event_service.log_space_task_event(user_id, updated.id, "update")
        return updated

    def complete(self, user_id, space_id: int, task_id: int, is_completed: bool):
        member = self.permission_service.require_member(space_id, user_id)
        task = self.get_task(user_id, space_id, task_id)
        if member.role == ROLE_VIEWER and task.assignee_id != user_id:
            raise_http(403, "VIEWER_CAN_COMPLETE_ONLY_ASSIGNED", "Viewer can complete only assigned tasks")
        if member.role not in {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER}:
            raise_http(403, "INSUFFICIENT_SPACE_ROLE", "Insufficient space role")
        updated = self.content_repository.set_task_completed(task, is_completed=is_completed, actor_id=user_id)
        self.sync_event_service.log_space_task_event(user_id, updated.id, "update")
        return updated

    def create_subtask(self, user_id, space_id: int, task_id: int, title: str, is_completed: bool = False):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        task = self.content_repository.get_task(space_id, task_id)
        if not task:
            raise_http(404, "SPACE_TASK_NOT_FOUND", "Space task not found")
        row = self.content_repository.create_subtask(task_id, title, is_completed, user_id)
        self.sync_event_service.log_space_subtask_event(user_id, row.id, "create")
        return row

    def list_subtasks(self, user_id, space_id: int, task_id: int):
        self.permission_service.require_member(space_id, user_id)
        task = self.content_repository.get_task(space_id, task_id)
        if not task:
            raise_http(404, "SPACE_TASK_NOT_FOUND", "Space task not found")
        return self.content_repository.list_subtasks(task_id)

    def update_subtask(self, user_id, space_id: int, task_id: int, subtask_id: int, title=None, is_completed=None):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        task = self.content_repository.get_task(space_id, task_id)
        if not task:
            raise_http(404, "SPACE_TASK_NOT_FOUND", "Space task not found")
        subtask = self.content_repository.get_subtask(task_id, subtask_id)
        if not subtask:
            raise_http(404, "SPACE_SUBTASK_NOT_FOUND", "Space subtask not found")
        updated = self.content_repository.update_subtask(subtask, user_id, title, is_completed)
        self.sync_event_service.log_space_subtask_event(user_id, updated.id, "update")
        return updated

    def delete_subtask(self, user_id, space_id: int, task_id: int, subtask_id: int):
        self.permission_service.require_role(space_id, user_id, {ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR})
        subtask = self.content_repository.get_subtask(task_id, subtask_id)
        if not subtask:
            raise_http(404, "SPACE_SUBTASK_NOT_FOUND", "Space subtask not found")
        deleted = self.content_repository.delete_subtask(subtask, user_id)
        self.sync_event_service.log_space_subtask_event(user_id, deleted.id, "delete")
        return deleted
