from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task import Task

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("/")
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()