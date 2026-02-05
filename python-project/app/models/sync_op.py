from sqlalchemy import Column, BigInteger, DateTime, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String

from .base import Base


class SyncOp(Base):
    __tablename__ = "sync_ops"
    __table_args__ = (
        UniqueConstraint("user_id", "op_id", name="uq_sync_ops_user_op_id"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    op_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    device_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
