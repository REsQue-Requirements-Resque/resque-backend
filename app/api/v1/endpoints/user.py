from fastapi import APIRouter

user_router = APIRouter()


@user_router.post("/register")
async def register():
    return {"message": "Register success"}


@user_router.get("/login")
async def login():
    return {"message": "Login success"}
