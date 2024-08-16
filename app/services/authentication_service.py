from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from app.models import User, LoginAttempt
from app.core.security import verify_password
from app.exceptions.user_exceptions import (
    InvalidCredentialsError,
    TooManyAttemptsError,
    DatabaseError,
)
from pydantic import ValidationError
from app.schemas.user import UserLogin
from datetime import datetime, timedelta, timezone


class AuthenticationService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.login_attempts = {}
        self.max_attempts = 5
        self.cooldown_period = timedelta(minutes=5)

    async def check_login_attempts(self, email: str, current_time: datetime) -> bool:
        # 쿨다운 기간이 지난 로그인 시도 삭제
        delete_query = delete(LoginAttempt).where(
            LoginAttempt.email == email,
            LoginAttempt.attempt_time <= current_time - self.cooldown_period
        )
        await self.db_session.execute(delete_query)
        await self.db_session.commit()

        # 최근 5분 동안의 로그인 시도 횟수 조회
        query = select(func.count(LoginAttempt.id)).where(
            LoginAttempt.email == email,
            LoginAttempt.attempt_time > current_time - self.cooldown_period,
        )
        result = await self.db_session.execute(query)
        attempt_count = result.scalar_one()

        if attempt_count >= self.max_attempts:
            return False

        # 새로운 로그인 시도 기록
        new_attempt = LoginAttempt(email=email, attempt_time=current_time)
        self.db_session.add(new_attempt)
        await self.db_session.commit()

        return True

    async def authenticate_user(
        self, email: str, password: str, current_time: datetime
    ) -> Optional[User]:
        if not await self.check_login_attempts(email, current_time):
            raise TooManyAttemptsError(
                "로그인 시도가 너무 많습니다. 나중에 다시 시도해 주세요."
            )

        # 사용자 인증 로직...
        user = await self.db_session.execute(select(User).where(User.email == email))
        user = user.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("잘못된 이메일 또는 비밀번호입니다.")

        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self.db_session.execute(
                select(User).filter(User.email == email)
            )
            return result.scalars().first()
        except Exception as e:
            raise DatabaseError(f"Error retrieving user: {str(e)}")

    async def record_failed_attempt(self, email: str) -> None:
        try:
            new_attempt = LoginAttempt(
                email=email, attempt_time=datetime.now(timezone.utc)
            )
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
