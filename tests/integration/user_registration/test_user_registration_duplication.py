import pytest
from sqlalchemy import delete, select

from app.exceptions.user_exceptions import DatabaseError, DuplicateEmailError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.req_1_basic_user_registration
class TestUserRegistrationDuplication:
    @classmethod
    def setup_class(cls):
        cls.emails = {
            "unique": "new@example.com",
            "existing": "existing@example.com",
            "case_insensitive": "EXISTING@example.com",
        }
        cls.passwords = {
            "valid": "ValidPass1!",
        }
        cls.names = {
            "valid": "John Doe",
        }

    @classmethod
    def get_valid_data(cls):
        return {
            "email": cls.emails["unique"],
            "password": cls.passwords["valid"],
            "name": cls.names["valid"],
        }

    @pytest.fixture(autouse=True)
    async def setup(self, db_session):
        # 테스트 실행 전 데이터베이스 정리
        await db_session.execute(delete(User))
        await db_session.commit()

        self.user_repository = UserRepository(db_session)

        # 기존 사용자 추가
        existing_user = User(
            email=self.emails["existing"],
            name=self.names["valid"],
            hashed_password="hashed_" + self.passwords["valid"],
        )
        db_session.add(existing_user)
        await db_session.commit()  # flush 대신 commit 사용

    async def test_register_user_with_unique_email(self):
        data = self.get_valid_data()
        user = await self.user_repository.create_user(UserCreate(**data))

        assert user is not None
        assert user.email == data["email"]
        assert await self.user_repository.get_user_by_email(data["email"]) is not None

    async def test_register_user_with_duplicate_email(self):
        data = self.get_valid_data()
        data["email"] = self.emails["existing"]

        with pytest.raises(DuplicateEmailError) as exc_info:
            await self.user_repository.create_user(UserCreate(**data))

        assert str(exc_info.value) == "Email already exists"

    async def test_register_user_with_case_insensitive_duplicate_email(self):
        data = self.get_valid_data()
        data["email"] = self.emails["case_insensitive"]

        with pytest.raises(DuplicateEmailError) as exc_info:
            await self.user_repository.create_user(UserCreate(**data))

        assert str(exc_info.value) == "Email already exists"

    async def test_database_error_during_user_creation(self, db_session):
        data = self.get_valid_data()

        async def fake_commit():
            raise Exception("Error")

        db_session.commit, original_commit = fake_commit, db_session.commit

        with pytest.raises(DatabaseError):
            await self.user_repository.create_user(UserCreate(**data))

        db_session.commit = original_commit
