from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def read_root():
    return {"message": settings.WELCOME_MESSAGE}
