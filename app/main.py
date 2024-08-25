from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.main_router import main_router
from app.core.config import settings
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the application")
    yield
    logger.info("Shutting down the application")


print(settings.PROJECT_NAME)
app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(main_router)

for route in app.routes:
    logger.info(f"Route: {route.path}, methods: {route.methods}")
