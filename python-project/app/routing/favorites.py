from fastapi import APIRouter, Depends
from app.depends import get_favorite_service
from app.services.favorite_service import FavoriteService
from app.schemas import TaskRead
from typing import List
from uuid import UUID

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.post("/add/{task_id}")
def add_favorite_task(
    task_id: int,
    user_id: UUID,
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    return favorite_service.add_favorite_task(task_id, user_id)

@router.get("/tasks", response_model=List[TaskRead])
def get_favorites_tasks(
    user_id: UUID,
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    return favorite_service.get_favorite_tasks(user_id)
