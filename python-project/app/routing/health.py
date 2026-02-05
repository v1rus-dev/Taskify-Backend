from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", summary="Health check", description="Returns service health status.")
async def health_check():
    return {"status": "ok", "service": "Taskify Backend"}
