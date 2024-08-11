import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.req_1_basic_user_registration
class TestUserRegistrationIntegration:
    REGISTER_URL = "/api/v1/users/register"

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession):
        # 테스트 전에 사용자 테이블을 비웁니다
        await db_session.execute(User.__table__.delete())
        await db_session.commit()

    async def test_user_registration_full_process(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        # 1. 유효한 사용자 데이터 준비
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User",
        }

        # 2. 회원가입 API 호출
        response = await client.post("/api/v1/users/register", json=user_data)

        # 3. 응답 검증
        assert response.status_code == 201
        response_data = response.json()
        assert "id" in response_data
        assert response_data["email"] == user_data["email"]
        assert response_data["name"] == user_data["name"]
        assert "password" not in response_data

        # 4. 데이터베이스에 사용자가 올바르게 저장되었는지 확인
        result = await db_session.execute(
            select(User).where(User.email == user_data["email"])
        )
        db_user = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.email == user_data["email"]
        assert db_user.name == user_data["name"]
        assert verify_password(user_data["password"], db_user.hashed_password)

        # 6. 중복 이메일로 회원가입 시도
        duplicate_response = await client.post("/api/v1/users/register", json=user_data)
        assert duplicate_response.status_code == 400
        assert "email already exists" in duplicate_response.json()["detail"].lower()

    async def test_user_registration_invalid_data(self, client: AsyncClient):
        # 유효하지 않은 데이터로 회원가입 시도
        invalid_user_data = {"email": "invalid-email", "password": "short", "name": ""}
        response = await client.post("/api/v1/users/register", json=invalid_user_data)
        assert response.status_code == 422
