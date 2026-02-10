"""
Файл внедрения зависимостей
"""
import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    HTTPBasic,
    HTTPBasicCredentials,
)
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.friend_repository import FriendRepository
from app.repositories.sync_event_repository import SyncEventRepository
from app.repositories.sync_op_repository import SyncOpRepository
from app.repositories.space_repository import SpaceRepository
from app.repositories.space_invite_repository import SpaceInviteRepository
from app.repositories.space_content_repository import SpaceContentRepository
from app.services.user_service import UserService
from app.services.task_service import TaskService
from app.services.auth_service import AuthService
from app.services.subtask_service import SubTaskService
from app.services.tag_service import TagService
from app.services.friend_service import FriendService
from app.services.cache_service import CacheService
from app.services.sync_event_service import SyncEventService
from app.services.sync_push_service import SyncPushService
from app.services.space_permission_service import SpacePermissionService
from app.services.space_interactor import SpaceInteractor
from app.services.space_list_interactor import SpaceListInteractor
from app.services.space_task_interactor import SpaceTaskInteractor
from app.services.space_note_interactor import SpaceNoteInteractor
from app.core.redis import get_redis_client
from app.core.security import decode_access_token
from app.errors import raise_http, error_detail
from uuid import UUID


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Создаёт репозиторий пользователей."""
    return UserRepository(db)


def get_task_repository(db: Session = Depends(get_db)) -> TaskRepository:
    """Создаёт репозиторий задач."""
    return TaskRepository(db)


def get_subtask_repository(db: Session = Depends(get_db)) -> SubTaskRepository:
    """Создаёт репозиторий подзадач."""
    return SubTaskRepository(db)

def get_tag_repository(db: Session = Depends(get_db)) -> TagRepository:
    """Создаёт репозиторий тегов."""
    return TagRepository(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Создаёт сервис пользователей."""
    user_repository = UserRepository(db)
    return UserService(user_repository)


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """Создаёт сервис задач."""
    task_repository = TaskRepository(db)
    user_repository = UserRepository(db)
    tag_repository = TagRepository(db)
    cache_service = CacheService(get_redis_client())
    sync_event_repository = SyncEventRepository(db)
    sync_event_service = SyncEventService(sync_event_repository)
    return TaskService(task_repository, user_repository, tag_repository, cache_service, sync_event_service)




def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Создаёт сервис аутентификации."""
    user_repository = UserRepository(db)
    return AuthService(user_repository)


def get_subtask_service(db: Session = Depends(get_db)) -> SubTaskService:
    """Создаёт сервис подзадач."""
    subtask_repository = SubTaskRepository(db)
    task_repository = TaskRepository(db)
    cache_service = CacheService(get_redis_client())
    sync_event_repository = SyncEventRepository(db)
    sync_event_service = SyncEventService(sync_event_repository)
    return SubTaskService(subtask_repository, task_repository, cache_service, sync_event_service)

def get_tag_service(db: Session = Depends(get_db)) -> TagService:
    """Создаёт сервис тегов."""
    tag_repository = TagRepository(db)
    return TagService(tag_repository)

def get_friend_service(db: Session = Depends(get_db)) -> FriendService:
    """Создаёт сервис друзей."""
    friend_repository = FriendRepository(db)
    return FriendService(friend_repository)


def get_sync_event_service(db: Session = Depends(get_db)) -> SyncEventService:
    """Создаёт сервис синхронизации изменений."""
    sync_event_repository = SyncEventRepository(db)
    return SyncEventService(sync_event_repository)


def get_sync_push_service(db: Session = Depends(get_db)) -> SyncPushService:
    """Создаёт сервис синхронизации клиента."""
    task_repository = TaskRepository(db)
    subtask_repository = SubTaskRepository(db)
    tag_repository = TagRepository(db)
    user_repository = UserRepository(db)
    sync_op_repository = SyncOpRepository(db)
    sync_event_service = SyncEventService(SyncEventRepository(db))
    space_repository = SpaceRepository(db)
    space_invite_repository = SpaceInviteRepository(db)
    space_content_repository = SpaceContentRepository(db)
    return SyncPushService(
        task_repository,
        subtask_repository,
        tag_repository,
        user_repository,
        sync_op_repository,
        sync_event_service,
        space_repository,
        space_invite_repository,
        space_content_repository,
    )


def get_space_repository(db: Session = Depends(get_db)) -> SpaceRepository:
    return SpaceRepository(db)


def get_space_invite_repository(db: Session = Depends(get_db)) -> SpaceInviteRepository:
    return SpaceInviteRepository(db)


def get_space_content_repository(db: Session = Depends(get_db)) -> SpaceContentRepository:
    return SpaceContentRepository(db)


def get_space_permission_service(db: Session = Depends(get_db)) -> SpacePermissionService:
    return SpacePermissionService(SpaceRepository(db))


def get_space_interactor(db: Session = Depends(get_db)) -> SpaceInteractor:
    space_repository = SpaceRepository(db)
    friend_repository = FriendRepository(db)
    invite_repository = SpaceInviteRepository(db)
    permission = SpacePermissionService(space_repository)
    sync_event_service = SyncEventService(SyncEventRepository(db))
    return SpaceInteractor(space_repository, friend_repository, invite_repository, permission, sync_event_service)


def get_space_list_interactor(db: Session = Depends(get_db)) -> SpaceListInteractor:
    space_repository = SpaceRepository(db)
    content_repository = SpaceContentRepository(db)
    permission = SpacePermissionService(space_repository)
    sync_event_service = SyncEventService(SyncEventRepository(db))
    return SpaceListInteractor(content_repository, permission, sync_event_service)


def get_space_task_interactor(db: Session = Depends(get_db)) -> SpaceTaskInteractor:
    space_repository = SpaceRepository(db)
    content_repository = SpaceContentRepository(db)
    permission = SpacePermissionService(space_repository)
    sync_event_service = SyncEventService(SyncEventRepository(db))
    return SpaceTaskInteractor(content_repository, space_repository, permission, sync_event_service)


def get_space_note_interactor(db: Session = Depends(get_db)) -> SpaceNoteInteractor:
    space_repository = SpaceRepository(db)
    content_repository = SpaceContentRepository(db)
    permission = SpacePermissionService(space_repository)
    sync_event_service = SyncEventService(SyncEventRepository(db))
    return SpaceNoteInteractor(content_repository, permission, sync_event_service)


auth_scheme = HTTPBearer()
admin_bearer_scheme = HTTPBearer(auto_error=False)
admin_basic_scheme = HTTPBasic(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    user_repository: UserRepository = Depends(get_user_repository)
):
    """Аутентификация через JWT."""
    if not credentials or not credentials.credentials:
        raise_http(
            status.HTTP_401_UNAUTHORIZED,
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
        )
    
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise_http(
            status.HTTP_401_UNAUTHORIZED,
            "TOKEN_VALIDATION_FAILED",
            "Token validation failed",
            details={"reason": str(exc)},
        )

    subject = payload.get("sub")
    if not subject:
        raise_http(
            status.HTTP_401_UNAUTHORIZED,
            "TOKEN_MISSING_SUB",
            "Token missing subject (sub) claim",
        )

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise_http(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_TOKEN_SUBJECT",
            "Invalid user ID format in token",
            details={"reason": str(exc)},
        )

    user = user_repository.get_by_id(user_id)
    if not user:
        raise_http(
            status.HTTP_401_UNAUTHORIZED,
            "USER_NOT_FOUND",
            "User not found",
            details={"user_id": str(user_id)},
        )
    return user


def require_admin(
    bearer_credentials: HTTPAuthorizationCredentials = Depends(admin_bearer_scheme),
    basic_credentials: HTTPBasicCredentials = Depends(admin_basic_scheme),
) -> None:
    if os.getenv("ENABLE_ADMIN", "false").lower() != "true":
        raise_http(status.HTTP_403_FORBIDDEN, "ADMIN_ACCESS_DISABLED", "Admin access is disabled")

    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and bearer_credentials and bearer_credentials.credentials:
        if bearer_credentials.credentials == admin_token:
            return
        raise_http(status.HTTP_403_FORBIDDEN, "INVALID_ADMIN_TOKEN", "Invalid admin token")

    basic_user = os.getenv("ADMIN_BASIC_USER")
    basic_password = os.getenv("ADMIN_BASIC_PASSWORD")
    if basic_user and basic_password and basic_credentials:
        is_user_match = secrets.compare_digest(basic_credentials.username, basic_user)
        is_pass_match = secrets.compare_digest(basic_credentials.password, basic_password)
        if is_user_match and is_pass_match:
            return
        raise_http(status.HTTP_403_FORBIDDEN, "INVALID_ADMIN_CREDENTIALS", "Invalid admin credentials")

    headers = None
    if os.getenv("ADMIN_BASIC_USER") and os.getenv("ADMIN_BASIC_PASSWORD"):
        headers = {"WWW-Authenticate": "Basic"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=error_detail("AUTH_HEADER_MISSING_OR_INVALID", "Authorization header missing or invalid"),
        headers=headers,
    )
