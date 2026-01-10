from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import engine
from app.models import Base, Task
from app.routers import routers

app = FastAPI(title="Tasky - Mini Todo API")

# Создаём таблицы при старте (только для разработки)
Base.metadata.create_all(bind=engine)

for router in routers:
    app.include_router(router)