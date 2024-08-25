from app.api.v1.router import api_v1_router
from fastapi import APIRouter
from app.core.logging import logger

main_router = APIRouter()

main_router.include_router(api_v1_router, prefix="/api/v1")
