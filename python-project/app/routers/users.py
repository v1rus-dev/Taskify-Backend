from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas import UserRead
from uuid import UUID

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/create/anonymous", response_model=UserRead)
def get_or_create_anonymous_user(db: Session = Depends(get_db)):
    """
    Создаёт нового анонимного пользователя и возвращает его user_id (UUID).
    """
    new_user = User(is_anonymous=True)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Получает пользователя по UUID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
