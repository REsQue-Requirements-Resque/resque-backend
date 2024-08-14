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
    async def test_brute_force_prevention(self):
        # Attempt to login 5 times with wrong password
        for _ in range(5):
            with pytest.raises(InvalidCredentialsError):
                await self.auth_service.authenticate_user(
                    "test@example.com", "wrongPassword"
                )

        # The 6th attempt should raise TooManyAttemptsError
        with pytest.raises(TooManyAttemptsError):
            await self.auth_service.authenticate_user(
                "test@example.com", "wrongPassword"
            )

        # Move time forward by 5 minutes
        with freeze_time("2023-01-01 12:05:01"):
            # Now the login should work with correct password
            user = await self.auth_service.authenticate_user(
                "test@example.com", "securePassword123!"
            )
            assert user is not None
            assert user.email == "test@example.com"

    async def test_login_attempts_reset_after_successful_login(self):
        # Attempt to login 4 times with wrong password
        for _ in range(4):
            with pytest.raises(InvalidCredentialsError):
                await self.auth_service.authenticate_user(
                    "test@example.com", "wrongPassword"
                )

        # Login successfully
        user = await self.auth_service.authenticate_user(
            "test@example.com", "securePassword123!"
        )
        assert user is not None

        # Check that login attempts have been reset
        result = await self.db_session.execute(
            select(LoginAttempt).filter(LoginAttempt.email == "test@example.com")
        )
        attempts = result.scalars().all()
        assert len(attempts) == 0
