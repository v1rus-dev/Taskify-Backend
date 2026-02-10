from .health import router as health_router
from .tasks import router as tasks_router
from .users import router as users_router
from .auth import router as auth_router
from .subtasks import router as subtasks_router
from .tags import router as tags_router
from .friends import router as friends_router
from .sync import router as sync_router
from .spaces import router as spaces_router
from .space_content import router as space_content_router
from .openapi import router as openapi_router

routers = [
    health_router,
    tasks_router,
    users_router,
    auth_router,
    subtasks_router,
    tags_router,
    friends_router,
    sync_router,
    spaces_router,
    space_content_router,
    openapi_router,
]
