from .helth import router as health_router
from .tasks import router as tasks_router
from .users import router as users_router
from .favorites import router as favorites_router

routers = [health_router, tasks_router, users_router, favorites_router]