from typing import List
from sqlalchemy.orm import Session

from app.models.sync_event import SyncEvent
from uuid import UUID


class SyncEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        entity: str,
        entity_id: int,
        op: str,
    ) -> SyncEvent:
        event = SyncEvent(
            user_id=user_id,
            entity=entity,
            entity_id=entity_id,
            op=op,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_changes(self, user_id: UUID, cursor: int, limit: int) -> List[SyncEvent]:
        return (
            self.db.query(SyncEvent)
            .filter(SyncEvent.user_id == user_id, SyncEvent.id > cursor)
            .order_by(SyncEvent.id.asc())
            .limit(limit)
            .all()
        )
