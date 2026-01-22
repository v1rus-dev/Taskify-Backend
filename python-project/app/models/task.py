from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy import and_
from .task_tag import task_tags
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
from .tag import Tag

class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="tasks")
    subtasks = relationship("SubTask", back_populates="task", cascade="all, delete-orphan")
    tags = relationship(
        "Tag",
        secondary=task_tags,
        primaryjoin="Task.id == task_tags.c.task_id",
        secondaryjoin=and_(
            Tag.id == task_tags.c.tag_id,
            Tag.user_id == task_tags.c.tag_user_id,
        ),
        back_populates="tasks",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
