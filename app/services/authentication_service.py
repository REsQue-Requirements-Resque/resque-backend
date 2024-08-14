from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models import User, LoginAttempt
from app.core.security import verify_password
from app.exceptions.user_exceptions import (
    InvalidCredentialsError,
    TooManyAttemptsError,
    DatabaseError,
)
from pydantic import ValidationError
from app.schemas.user import UserLogin
from datetime import datetime, timedelta


class AuthenticationService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        try:
            user_login = UserLogin(email=email, password=password)
        except ValidationError:
            raise InvalidCredentialsError("Invalid email or password format")

        if not await self.check_login_attempts(user_login.email):
            raise TooManyAttemptsError(
                "Too many login attempts. Please try again later."
            )

        user = await self.get_user_by_email(user_login.email)
        if not user or not verify_password(user_login.password, user.hashed_password):
            await self.record_failed_attempt(user_login.email)
            raise InvalidCredentialsError("Invalid email or password")

        await self.reset_login_attempts(user_login.email)
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self.db_session.execute(
                select(User).filter(User.email == email)
            )
            return result.scalars().first()
        except Exception as e:
            raise DatabaseError(f"Error retrieving user: {str(e)}")

    async def check_login_attempts(self, email: str) -> bool:
        try:
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            result = await self.db_session.execute(
                select(LoginAttempt)
                .filter(LoginAttempt.email == email)
                .filter(LoginAttempt.attempt_time > five_minutes_ago)
            )
            attempts = result.scalars().all()
            return len(attempts) < 5
        except Exception as e:
            raise DatabaseError(f"Error checking login attempts: {str(e)}")

    async def record_failed_attempt(self, email: str) -> None:
        try:
            new_attempt = LoginAttempt(email=email, attempt_time=datetime.utcnow())
            self.db_session.add(new_attempt)
            await self.db_session.commit()
        except Exception as e:
            await self.db_session.rollback()
            raise DatabaseError(f"Error recording failed attempt: {str(e)}")

    async def reset_login_attempts(self, email: str) -> None:
        try:
            await self.db_session.execute(
                delete(LoginAttempt).where(LoginAttempt.email == email)
            )
            await self.db_session.commit()
        except Exception as e:
            await self.db_session.rollback()
            raise DatabaseError(f"Error resetting login attempts: {str(e)}")
