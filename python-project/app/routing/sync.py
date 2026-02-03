from fastapi import APIRouter, Depends, Query
from typing import List, Tuple, Dict

from app.depends import get_current_user, get_sync_event_service, get_sync_push_service
from app.schemas import SyncChangesRead, SyncPushRequest, SyncPushResponse
from app.models.user import User
from app.services.sync_event_service import SyncEventService
from app.services.sync_push_service import SyncPushService


router = APIRouter(prefix="/sync", tags=["Sync"])


@router.get("/changes", response_model=SyncChangesRead)
def get_changes(
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    compact: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    sync_event_service: SyncEventService = Depends(get_sync_event_service),
):
    events = sync_event_service.get_changes(current_user.id, cursor, limit)
    next_cursor = events[-1].id if events else cursor
    if compact and events:
        latest_by_entity: Dict[Tuple[str, int], int] = {}
        for idx, event in enumerate(events):
            latest_by_entity[(event.entity, event.entity_id)] = idx
        events = [events[idx] for idx in sorted(latest_by_entity.values())]
    changes = sync_event_service.build_changes(current_user.id, events)
    return SyncChangesRead(next_cursor=next_cursor, changes=changes)


@router.post("/push", response_model=SyncPushResponse)
def push_changes(
    payload: SyncPushRequest,
    current_user: User = Depends(get_current_user),
    sync_push_service: SyncPushService = Depends(get_sync_push_service),
):
    return sync_push_service.process(current_user.id, payload.device_id, payload.ops)
