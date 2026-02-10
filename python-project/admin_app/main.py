import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqladmin import Admin

from admin_app.auth import AdminAuthBackend
from admin_app.views import register_admin_views
from app.core.logging import configure_logging, register_request_logging
from app.database import engine

app = FastAPI(title="Taskify Admin")
configure_logging(service_name="admin", log_file=os.getenv("LOG_FILE", "python-project/app/logs/admin.log"))
register_request_logging(app, service_name="admin", logger_name="admin.request")

auth_backend = AdminAuthBackend(
    secret_key=os.getenv("ADMIN_SESSION_SECRET", "taskify-admin-session-secret")
)
admin = Admin(app=app, engine=engine, authentication_backend=auth_backend, title="Taskify Admin")
register_admin_views(admin)


@app.get("/", include_in_schema=False)
def _root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/admin", status_code=302)
