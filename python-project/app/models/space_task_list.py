from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class SpaceTaskList(Base):
    __tablename__ = "space_task_lists"
    __table_args__ = (
        UniqueConstraint("space_id", "client_id", name="uq_space_task_lists_space_client_id"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    space_id = Column(BigInteger, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    order = Column(BigInteger, nullable=False, default=0)
    client_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
