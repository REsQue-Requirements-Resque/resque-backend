from app.api.v1.router import api_v1_router
from fastapi import APIRouter

main_router = APIRouter()

main_router.include_router(api_v1_router, prefix="/v1")
