from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User
from app.core.security import verify_password
from app.exceptions.user_exceptions import (
    InvalidCredentialsError,
    TooManyAttemptsError,
    DatabaseError,
)


class AuthenticationServiceImpl:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def authenticate_user(self, email: str, password: str) -> User:
        if not await self.check_login_attempts(email):
            raise TooManyAttemptsError(
                "Too many login attempts. Please try again later."
            )

        user = await self.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            await self.record_failed_attempt(email)
            raise InvalidCredentialsError("Invalid email or password")

        await self.reset_login_attempts(email)
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
        # 이 메서드는 로그인 시도 횟수를 확인하고 제한을 초과했는지 여부를 반환합니다.
        # 실제 구현에서는 데이터베이스나 캐시에서 로그인 시도 횟수를 조회해야 합니다.
        # 여기서는 간단히 True를 반환하는 것으로 대체합니다.
        return True

    async def record_failed_attempt(self, email: str) -> None:
        # 이 메서드는 실패한 로그인 시도를 기록합니다.
        # 실제 구현에서는 데이터베이스나 캐시에 기록해야 합니다.
        pass

    async def reset_login_attempts(self, email: str) -> None:
        # 이 메서드는 성공적인 로그인 후 로그인 시도 횟수를 초기화합니다.
        # 실제 구현에서는 데이터베이스나 캐시의 기록을 초기화해야 합니다.
        pass
