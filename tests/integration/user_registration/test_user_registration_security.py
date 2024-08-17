import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.security
@pytest.mark.req_1_basic_user_registration
class TestUserRegistrationSecurity:
    @classmethod
    def setup_class(cls):
        cls.emails = {
            "existing": "existing@gmail.com",
            "unique": "unique@gmail.com",
        }
        cls.passwords = {
            "valid": "SecurePass123!",
        }
        cls.names = {
            "valid": "Test User",
        }

    @classmethod
    def get_valid_data(cls):
        return {
            "email": cls.emails["unique"],
            "password": cls.passwords["valid"],
            "name": cls.names["valid"],
        }

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession):
        # 테스트 실행 전 데이터베이스 정리
        await db_session.execute(delete(User))
        await db_session.commit()

        self.user_repository = UserRepository(db_session)
        existing_user = User(
            email=self.emails["existing"],
            name=self.names["valid"],
            hashed_password=get_password_hash(self.passwords["valid"]),
        )
        db_session.add(existing_user)
        await db_session.commit()  # flush 대신 commit 사용

    async def test_password_hashing(self, db_session: AsyncSession):
        user_data = self.get_valid_data()
        user_create = UserCreate(**user_data)
        created_user = await self.user_repository.create_user(user_create)

        assert created_user.hashed_password != user_data["password"]
        assert created_user.hashed_password != get_password_hash(user_data["password"])

    async def test_hashed_password_verification(self, db_session: AsyncSession):
        user_data = self.get_valid_data()
        user_create = UserCreate(**user_data)
        created_user = await self.user_repository.create_user(user_create)

        assert verify_password(user_data["password"], created_user.hashed_password)

    async def test_password_not_stored_in_plaintext(self, db_session: AsyncSession):
        user_data = self.get_valid_data()
        user_data["email"] = "another@example.com"
        user_create = UserCreate(**user_data)
        created_user = await self.user_repository.create_user(user_create)

        result = await db_session.execute(
            select(User).filter_by(email=user_data["email"])
        )
        stored_user = result.scalar_one_or_none()
        assert stored_user is not None
        assert user_data["password"] not in stored_user.hashed_password
        assert get_password_hash(user_data["password"]) != stored_user.hashed_password
