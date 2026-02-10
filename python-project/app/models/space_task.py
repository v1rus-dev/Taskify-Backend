from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class SpaceTask(Base):
    __tablename__ = "space_tasks"
    __table_args__ = (
        UniqueConstraint("space_id", "client_id", name="uq_space_tasks_space_client_id"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    space_id = Column(BigInteger, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    list_id = Column(BigInteger, ForeignKey("space_task_lists.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    claimed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    client_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
