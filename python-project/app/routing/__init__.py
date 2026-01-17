from .health import router as health_router
from .tasks import router as tasks_router
from .users import router as users_router
from .auth import router as auth_router
from .admin import router as admin_router

routers = [health_router, tasks_router, users_router, auth_router, admin_router]
