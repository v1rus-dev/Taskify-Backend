from sqlalchemy import Table, Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


user_friends = Table(
    "user_friends",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("friend_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)
