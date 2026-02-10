from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class SpaceInvite(Base):
    __tablename__ = "space_invites"
    __table_args__ = (
        UniqueConstraint("token", name="uq_space_invites_token"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    space_id = Column(BigInteger, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    inviter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)
    token = Column(String(128), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
