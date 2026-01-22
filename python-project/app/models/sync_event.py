from sqlalchemy import Column, BigInteger, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class SyncEvent(Base):
    __tablename__ = "sync_events"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    entity = Column(String(32), nullable=False)
    entity_id = Column(BigInteger, nullable=False)
    op = Column(String(16), nullable=False)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
