from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.routers import routers

app = FastAPI(title="Tasky - Mini Todo API")

# Создаём таблицы при старте (только для разработки)
Base.metadata.create_all(bind=engine)

for router in routers:
    app.include_router(router)