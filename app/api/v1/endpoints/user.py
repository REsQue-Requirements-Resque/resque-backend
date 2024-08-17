import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    check_brute_force,
    clear_login_attempts,
    create_access_token,
    get_current_user,
    verify_password,
)
from app.db.base import get_async_db
from app.exceptions.user_exceptions import (
    DatabaseError,
    DuplicateEmailError,
    InvalidCredentialsError,
    TooManyAttemptsError,
)
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse

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

        # 브루트 포스 체크
        try:
            logger.debug("Checking brute force")
            await check_brute_force(form_data.username, db)
        except SQLAlchemyError as e:
            logger.error(f"Database error during brute force check: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred",
            )

        # 사용자 조회
        try:
            logger.debug("Getting user from repository")
            user = await repo.get_user_by_email(form_data.username)
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred",
            )

        # 인증
        if user is None or not verify_password(
            form_data.password, user.hashed_password
        ):
            logger.warning(f"Invalid credentials for user: {form_data.username}")
            try:
                await repo.record_failed_attempt(form_data.username)
            except SQLAlchemyError as e:
                logger.error(f"Database error while recording failed attempt: {str(e)}")
            raise InvalidCredentialsError()

        # 로그인 성공 처리
        try:
            logger.debug("Clearing login attempts")
            await clear_login_attempts(form_data.username, db)
        except SQLAlchemyError as e:
            logger.error(f"Database error while clearing login attempts: {str(e)}")
            # 이 오류는 로그인 성공에 치명적이지 않으므로 계속 진행

        # 토큰 생성
        logger.debug("Creating access token")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        logger.info(f"Login successful for user: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    except TooManyAttemptsError:
        logger.warning(f"Too many login attempts for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidCredentialsError:
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(user: UserResponse = Depends(get_current_user)):
    return user
