import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.main import app
from app.models.user import User
from app.core.security import verify_password


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
@pytest.mark.req_1_basic_user_registration
class TestUserRegistrationAPI:
    REGISTER_URL = "/api/v1/users/register"

    @pytest.fixture(scope="class")
    async def async_client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession):
        await db_session.execute(delete(User))
        await db_session.commit()

    async def test_register_user_success(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User",
        }
        response = await async_client.post(self.REGISTER_URL, json=user_data)

        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["email"] == user_data["email"]
        assert response.json()["name"] == user_data["name"]
        assert "password" not in response.json()

        result = await db_session.execute(
            select(User).filter(User.email == user_data["email"])
        )
        db_user: User = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.email == user_data["email"]
        assert db_user.name == user_data["name"]
        assert verify_password(user_data["password"], db_user.hashed_password)

    async def test_register_user_duplicate_email(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        user_data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "name": "Existing User",
        }
        await async_client.post(self.REGISTER_URL, json=user_data)
        response = await async_client.post(self.REGISTER_URL, json=user_data)

        assert response.status_code == 400
        assert "detail" in response.json()

    async def test_register_user_invalid_data(self, async_client: AsyncClient):
        invalid_data = {"email": "invalid-email", "password": "short", "name": ""}
        response = await async_client.post(self.REGISTER_URL, json=invalid_data)

        assert response.status_code == 422
        assert "detail" in response.json()

    async def test_register_user_missing_data(self, async_client: AsyncClient):
        incomplete_data = {"email": "incomplete@example.com"}
        response = await async_client.post(self.REGISTER_URL, json=incomplete_data)

        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.parametrize(
        "invalid_password",
        [
            "short",
            "onlylowercase",
            "ONLYUPPERCASE",
            "NoSpecialChar1",
            "NoNumber!",
        ],
    )
    async def test_register_user_invalid_password(
        self, async_client: AsyncClient, invalid_password
    ):
        user_data = {
            "email": "testuser@example.com",
            "password": invalid_password,
            "name": "Test User",
        }
        response = await async_client.post(self.REGISTER_URL, json=user_data)

        assert response.status_code == 422
        assert "detail" in response.json()

    def print_response(self, response):
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {response.json()}")
