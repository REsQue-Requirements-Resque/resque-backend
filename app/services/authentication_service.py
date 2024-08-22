from fastapi import HTTPException, status
from jose import JWTError, jwt
from app.core.config import settings
from app.schemas.token import TokenData
from app.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)


class AuthenticationService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    @staticmethod
    def decode_token(token: str) -> TokenData:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username: str | None = payload.get("sub")
            if username is None:
                raise ValueError("Username not found in token")
            return TokenData(username=username)
        except JWTError:
            raise ValueError("Invalid token")

    async def get_current_user(self, token: str):
        try:
            token_data = self.decode_token(token)
            user = await self.user_repository.get_by_username(token_data.username)
            if user is None:
                raise ValueError("User not found")
            return user
        except ValueError as e:
            logger.error(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    async def get_user(self, username: str):
        try:
            user = await self.user_repository.get_by_username(username)
            if user is None:
                logger.info(f"User with username {username} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with username {username} not found",
                )
            return user
        except HTTPException:
            # Re-raise HTTP exceptions without modifying them
            raise
        except Exception as e:
            logger.error(f"An error occurred while retrieving the user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving the user",
            ) from e
