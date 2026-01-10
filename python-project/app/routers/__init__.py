from .helth import router as health_router
from .tasks import router as tasks_router

routers = [health_router, tasks_router]