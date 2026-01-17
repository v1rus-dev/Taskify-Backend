from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base


class SubTask(Base):
    __tablename__ = "subtasks"

    id = Column(BigInteger, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    task_id = Column(BigInteger, ForeignKey("tasks.id"), nullable=False, index=True)
    task = relationship("Task", back_populates="subtasks")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
