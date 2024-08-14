import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from datetime import timedelta
import asyncio

from app.main import app
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models import User, LoginAttempt
from app.services.authentication_service import AuthenticationService
from app.core.config import settings
from freezegun import freeze_time


@pytest.mark.asyncio
class TestLoginIntegration:
    LOGIN_URL = "/api/v1/users/login"
    ME_URL = "/api/v1/users/me"

    @pytest.fixture(autouse=True)
    async def setup(self, client: AsyncClient, db_session: AsyncSession):
        self.client = client
        self.db_session = db_session
        self.auth_service = AuthenticationService(db_session)

        test_user_data = self.get_test_user_data()

        hashed_password = get_password_hash(password=test_user_data["password"])
        test_user = User(email=test_user_data["email"], hashed_password=hashed_password)
        self.db_session.add(test_user)
        await self.db_session.commit()

        # Verify the user was created
        result = await self.db_session.execute(
            select(User).filter(User.email == test_user_data["email"])
        )
        created_user = result.scalar_one_or_none()
        assert created_user is not None, f"Test user was not created: {test_user_data["email"]}"
        print(f"Test user created: {created_user.email}")

        yield

        # Cleanup
        await self.db_session.execute(User.__table__.delete())
        await self.db_session.execute(LoginAttempt.__table__.delete())
        await self.db_session.commit()

    def get_test_user_data(self):
        return {
            "email": "test@example.com",
            "password": "securePassword123!",
        }

    def get_test_user_request(self):
        data = self.get_test_user_data()

        return {
            "username": data["email"],
            "password": data["password"],
        }

    async def test_login_success(self):
        response = await self.client.post(
            self.LOGIN_URL,
            data=self.get_test_user_request(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

        # Verify JWT token
        token = data["access_token"]
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == "test@example.com"

    async def test_login_failure(self):
        response = await self.client.post(
            self.LOGIN_URL,
            data={"username": self.get_test_user_data()["email"], "password": "wrongPassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    async def test_password_hashing_and_verification(self):
        password = "securePassword123!"
        hashed_password = get_password_hash(password)
        assert verify_password(
            password, hashed_password
        ), "Password verification failed"
        assert not verify_password(
            "wrongpassword", hashed_password
        ), "Incorrect password was verified"

    async def test_protected_route(self):
        # First, login to get the token
        login_response = await self.client.post(
            self.LOGIN_URL,
            data=self.get_test_user_request(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        print(f"Login response status: {login_response.status_code}")
        print(f"Login response content: {login_response.content}")

        if login_response.status_code != 200:
            # Get more details about the user in the database
            result = await self.db_session.execute(
                select(User).filter(User.email == "test123456@example.com")
            )
            user = result.scalar_one_or_none()
            if user:
                print(f"User exists in DB: {user.email}")
                print(f"Stored hashed password: {user.hashed_password}")
            else:
                print("User does not exist in the database")

        assert (
            login_response.status_code == 200
        ), f"Login failed: {login_response.content}"

    async def test_password_hashing_comparison(self):
        password = "securePassword123!"
        hashed_password = get_password_hash(password)

        assert verify_password(password, hashed_password)
        assert not verify_password("wrongPassword", hashed_password)
        
    async def test_https_secure_connection(self, httpsclient: AsyncClient):
        data = self.get_test_user_request()
        response = await httpsclient.post(
            self.LOGIN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert str(response.url).startswith("https://")
        assert response.status_code == 200

    async def test_brute_force_prevention(self, client: AsyncClient, test_user: User):
        with freeze_time("2023-01-01 12:00:00"):
            # Attempt to login 5 times with wrong password
            for _ in range(5):
                response = await client.post(
                    self.LOGIN_URL,
                    data={"username": test_user.email, "password": "wrongPassword"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                assert response.status_code == 401

            # The 6th attempt should be blocked
            response = await client.post(
                self.LOGIN_URL,
                data={"username": test_user.email, "password": "wrongPassword"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 429
            assert "Too many login attempts" in response.json()["detail"]

        # Move time forward by 15 minutes
        with freeze_time("2023-01-01 12:15:01"):
            # Now the login should work with correct password
            response = await client.post(
                self.LOGIN_URL,
                data={"username": test_user.email, "password": "securePassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 200

    async def test_login_attempts_reset_after_successful_login(self):
        # Attempt to login 4 times with wrong password
        for _ in range(4):
            response = await self.client.post(
                self.LOGIN_URL,
                data={"username": "test@example.com", "password": "wrongPassword"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 401

        # Login successfully
        response = await self.client.post(
            self.LOGIN_URL,
            data={"username": "test@example.com", "password": "securePassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200

        # Check that login attempts have been reset
        result = await self.db_session.execute(
            select(LoginAttempt).filter(LoginAttempt.email == "test@example.com")
        )
        attempts = result.scalars().all()
        assert len(attempts) == 0

    async def test_token_expiration(self):
        # Create a short-lived token
        access_token = create_access_token(
            data={"sub": "test@example.com"}, expires_delta=timedelta(seconds=1)
        )

        # Wait for the token to expire
        await asyncio.sleep(2)

        # Try to access a protected route with the expired token
        response = await self.client.get(
            self.ME_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Token has expired"
