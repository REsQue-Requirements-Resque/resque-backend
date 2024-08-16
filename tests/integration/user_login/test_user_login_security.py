import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_password_hash, verify_password
from app.models import User, LoginAttempt
from app.services.authentication_service import AuthenticationService
from app.exceptions.user_exceptions import TooManyAttemptsError, InvalidCredentialsError
from freezegun import freeze_time
from httpx import AsyncClient
from datetime import datetime, timezone


@pytest.mark.asyncio
class TestLoginSecurity:
    @pytest.fixture(autouse=True)
    async def setup(self, client: TestClient, db_session: AsyncSession):
        self.client = client
        self.db_session = db_session
        self.auth_service = AuthenticationService(db_session)

        # Create a test user
        hashed_password = get_password_hash("securePassword123!")
        test_user = User(email="test@example.com", hashed_password=hashed_password)
        self.db_session.add(test_user)
        await self.db_session.commit()

        yield

        # Cleanup
        await self.db_session.execute(User.__table__.delete())
        await self.db_session.execute(LoginAttempt.__table__.delete())
        await self.db_session.commit()

    async def test_password_hashing_comparison(self):
        password = "securePassword123!"
        hashed_password = get_password_hash(password)

        assert verify_password(password, hashed_password)
        assert not verify_password("wrongPassword", hashed_password)

    async def test_https_secure_connection(self, httpsclient: AsyncClient):
        response = await httpsclient.get("/api/v1")
        assert str(response.url).startswith("https://")
        assert response.status_code == 200

    @freeze_time("2023-01-01 12:00:00")
    async def test_consecutive_failed_attempts_cause_lockout(self):
        current_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # 5번의 실패한 로그인 시도
        for _ in range(5):
            with pytest.raises(InvalidCredentialsError):
                await self.auth_service.authenticate_user(
                    "test@example.com", "wrongPassword", current_time
                )

        # 6번째 시도에서 TooManyAttemptsError 발생
        with pytest.raises(TooManyAttemptsError):
            await self.auth_service.authenticate_user(
                "test@example.com", "wrongPassword", current_time
            )

    @freeze_time("2023-01-01 12:00:00")
    async def test_successful_login_after_cooldown(self):
        current_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # 5번의 실패한 로그인 시도
        for _ in range(5):
            with pytest.raises(InvalidCredentialsError):
                await self.auth_service.authenticate_user(
                    "test@example.com", "wrongPassword", current_time
                )

        # 쿨다운 기간 후 로그인 성공
        with freeze_time("2023-01-01 12:05:01"):
            current_time = datetime(2023, 1, 1, 12, 5, 1, tzinfo=timezone.utc)
            user = await self.auth_service.authenticate_user(
                "test@example.com", "securePassword123!", current_time
            )
            assert user is not None

    @freeze_time("2023-01-01 12:00:00")
    async def test_lockout_resets_after_cooldown(self):
        current_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # 5번의 실패한 로그인 시도
        for _ in range(5):
            with pytest.raises(InvalidCredentialsError):
                await self.auth_service.authenticate_user(
                    "test@example.com", "wrongPassword", current_time
                )

        # 쿨다운 후 다시 5번의 실패한 시도가 가능
        with freeze_time("2023-01-01 12:05:02"):
            current_time = datetime(2023, 1, 1, 12, 5, 2, tzinfo=timezone.utc)
            for _ in range(5):
                with pytest.raises(InvalidCredentialsError):
                    await self.auth_service.authenticate_user(
                        "test@example.com", "wrongPassword", current_time
                    )

            # 6번째 시도에서 다시 TooManyAttemptsError 발생
            with pytest.raises(TooManyAttemptsError):
                await self.auth_service.authenticate_user(
                    "test@example.com", "wrongPassword", current_time
                )
