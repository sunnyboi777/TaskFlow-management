import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .core.database import Base, engine
from . import models

from .api.routes.tasks import router as tasks_router
from .api.routes.auth import router as auth_router
from .api.routes.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    expected_database = os.getenv(
        "EXPECTED_DATABASE_NAME",
        "taskproject",
    )

    if expected_database and database_name != expected_database:
        raise RuntimeError(
            f"Wrong database! Expected {expected_database}, "
            f"got {database_name}"
        )

    print(f"Database connected successfully: {database_name}")

    yield


app = FastAPI(
    title="Task Management API",
    description="CRUD operations using FastAPI and PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    return {
        "message": "Task Management API is running",
        "database": database_name,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(tasks_router)
app.include_router(auth_router)
app.include_router(admin_router)
