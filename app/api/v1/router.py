from fastapi import APIRouter
from app.api.v1.endpoints import root, user

api_router = APIRouter()

api_router.include_router(root.router, tags=["root"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
