from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.routing import routers

app = FastAPI(title="Taskify - Mini Todo API")

# Создаём таблицы при старте (только для разработки)
Base.metadata.create_all(bind=engine)

for router in routers:
    app.include_router(router)