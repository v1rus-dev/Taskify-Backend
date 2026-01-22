from .health import router as health_router
from .tasks import router as tasks_router
from .users import router as users_router
from .auth import router as auth_router
from .subtasks import router as subtasks_router
from .tags import router as tags_router

routers = [health_router, tasks_router, users_router, auth_router, subtasks_router, tags_router]
