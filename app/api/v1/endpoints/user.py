from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_async_db
from app.schemas.user import UserCreate, UserResponse
from app.repositories.user_repository import UserRepository
from app.exceptions.user_exceptions import DuplicateEmailError, DatabaseError
import logging

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
