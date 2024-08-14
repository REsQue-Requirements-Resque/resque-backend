from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_async_db
from app.schemas.user import UserCreate, UserResponse
from app.repositories.user_repository import UserRepository
from app.core.security import (
    create_access_token,
    verify_password,
    get_current_user,
    check_brute_force,
    clear_login_attempts,
)
from app.exceptions.user_exceptions import (
    DuplicateEmailError,
    DatabaseError,
    InvalidCredentialsError,
)
import logging
from datetime import timedelta
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_user_repository(
    db: AsyncSession = Depends(get_async_db),
) -> UserRepository:
    return UserRepository(db)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user: UserCreate,
    repo: UserRepository = Depends(get_user_repository),
):
    try:
        db_user = await repo.create_user(user)
        logger.info(f"User registered successfully: {db_user.email}")
        return db_user
    except DuplicateEmailError:
        logger.warning(f"Registration attempt with duplicate email: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )
    except DatabaseError as e:
        logger.error(f"Database error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request",
        )


@router.post("/login")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        logger.info(f"Login attempt for user: {form_data.username}")
        user = await repo.get_user_by_email(form_data.username)
        if user is None:
            logger.warning(f"User not found: {form_data.username}")
            raise InvalidCredentialsError()

        if not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Invalid password for user: {form_data.username}")
            await check_brute_force(form_data.username, db)  # 여기로 이동
            raise InvalidCredentialsError()

        await clear_login_attempts(form_data.username, db)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        logger.info(f"Login successful for user: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    except InvalidCredentialsError:
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(user: UserResponse = Depends(get_current_user)):
    return user
