from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, func
from .base import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)