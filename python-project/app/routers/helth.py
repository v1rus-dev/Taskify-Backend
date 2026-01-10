from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task import Task

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    return {"status": "ok", "service": "Tasky Backend"}