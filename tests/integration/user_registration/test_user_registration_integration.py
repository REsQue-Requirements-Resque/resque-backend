import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password
import logging

logger = logging.getLogger(__name__)


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
        response = await client.post(self.REGISTER_URL, json=user_data)

        # 로깅 추가
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.content}")

        # 3. 응답 검증
        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}. Response: {response.content}"

        # 4. 응답 데이터 검증
        response_data = response.json()
        assert "id" in response_data
        assert response_data["email"] == user_data["email"]
        assert response_data["name"] == user_data["name"]
        assert "password" not in response_data

    async def test_user_registration_invalid_data(self, client: AsyncClient):
        # 유효하지 않은 데이터로 회원가입 시도
        invalid_user_data = {"email": "invalid-email", "password": "short", "name": ""}
        response = await client.post(self.REGISTER_URL, json=invalid_user_data)
        assert response.status_code == 422
