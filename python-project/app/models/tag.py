from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
from .task_tag import task_tags


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("user_id", "is_user_tag", "name", "color", name="uq_tags_identity"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    is_user_tag = Column(Boolean, nullable=False, default=True)
    name = Column(String(128), nullable=True)
    color = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="tags")
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")


Index("ix_tags_user_id_name", Tag.user_id, Tag.name)
