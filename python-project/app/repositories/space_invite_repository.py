from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.space_invite import SpaceInvite


class SpaceInviteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_invite(self, space_id: int, inviter_id, role: str, token: str, expires_at: datetime) -> SpaceInvite:
        invite = SpaceInvite(
            space_id=space_id,
            inviter_id=inviter_id,
            role=role,
            token=token,
            expires_at=expires_at,
            status="active",
        )
        self.db.add(invite)
        self.db.commit()
        self.db.refresh(invite)
        return invite

    def list_invites(self, space_id: int) -> List[SpaceInvite]:
        return (
            self.db.query(SpaceInvite)
            .filter(SpaceInvite.space_id == space_id)
            .order_by(SpaceInvite.created_at.desc())
            .all()
        )

    def get_invite(self, invite_id: int) -> Optional[SpaceInvite]:
        return self.db.query(SpaceInvite).filter(SpaceInvite.id == invite_id).first()

    def get_by_token(self, token: str) -> Optional[SpaceInvite]:
        return self.db.query(SpaceInvite).filter(SpaceInvite.token == token).first()

    def revoke(self, invite: SpaceInvite) -> SpaceInvite:
        invite.status = "revoked"
        self.db.commit()
        self.db.refresh(invite)
        return invite
