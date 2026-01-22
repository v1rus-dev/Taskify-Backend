from sqlalchemy import Table, Column, BigInteger, ForeignKey, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", BigInteger, primary_key=True),
    Column("tag_user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    ForeignKeyConstraint(
        ["tag_id", "tag_user_id"],
        ["tags.id", "tags.user_id"],
        ondelete="CASCADE",
    ),
)
