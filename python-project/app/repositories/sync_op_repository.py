from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.models.sync_op import SyncOp


class SyncOpRepository:
    def __init__(self, db: Session):
        self.db = db

    def exists(self, user_id: UUID, op_id: UUID) -> bool:
        return (
            self.db.query(SyncOp)
            .filter(SyncOp.user_id == user_id, SyncOp.op_id == op_id)
            .first()
            is not None
        )

    def create(self, user_id: UUID, op_id: UUID, device_id: Optional[UUID]) -> SyncOp:
        op = SyncOp(user_id=user_id, op_id=op_id, device_id=device_id)
        self.db.add(op)
        self.db.commit()
        self.db.refresh(op)
        return op
