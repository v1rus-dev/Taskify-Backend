import os

from fastapi import FastAPI
from sqladmin import Admin
from starlette.routing import Route

from admin_app.auth import AdminAuthBackend
from admin_app.logs_view import LogsView, PgAdminView, logs_stream_handler
from admin_app.views import register_admin_views
from app.core.logging import configure_logging, register_request_logging
from app.database import engine

app = FastAPI(title="Taskify Admin")
configure_logging(service_name="admin", log_file=os.getenv("LOG_FILE", "python-project/app/logs/admin.log"))
register_request_logging(app, service_name="admin", logger_name="admin.request")

auth_backend = AdminAuthBackend(
    secret_key=os.getenv("ADMIN_SESSION_SECRET", "taskify-admin-session-secret")
)
admin = Admin(app=app, engine=engine, authentication_backend=auth_backend, title="Taskify Admin", base_url="/")
admin.admin.routes.insert(0, Route("/logs-stream", logs_stream_handler, methods=["GET"], name="logs-stream"))
register_admin_views(admin)
admin.add_view(LogsView)
admin.add_view(PgAdminView)
