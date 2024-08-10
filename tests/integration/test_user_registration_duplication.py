import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from app.schemas.users import UserCreate
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.exceptions.user_exceptions import DuplicateEmailError, DatabaseError


@pytest.mark.unit
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

    def test_register_user_with_unique_email(self, db_session):
        user_repository = UserRepository(db_session)
        data = self.get_valid_data()

        user = user_repository.create_user(**data)

        assert user is not None
        assert user.email == data["email"]
        assert db_session.query(User).filter_by(email=data["email"]).first() is not None

    def test_register_user_with_duplicate_email(self, db_session):
        user_repository = UserRepository(db_session)
        # 기존 사용자 생성
        existing_user = User(
            email=self.emails["existing"],
            password=self.passwords["valid"],
            name=self.names["valid"],
        )
        db_session.add(existing_user)
        db_session.commit()

        data = self.get_valid_data()
        data["email"] = self.emails["existing"]

        with pytest.raises(DuplicateEmailError) as exc_info:
            user_repository.create_user(**data)

        assert str(exc_info.value) == "Email already exists"

    def test_register_user_with_case_insensitive_duplicate_email(self, db_session):
        user_repository = UserRepository(db_session)
        data = self.get_valid_data()
        data["email"] = self.emails["case_insensitive"]

        with pytest.raises(DuplicateEmailError) as exc_info:
            user_repository.create_user(**data)

        assert str(exc_info.value) == "Email already exists"

    def test_database_error_during_duplication_check(self, db_session, mocker):
        user_repository = UserRepository(db_session)
        data = self.get_valid_data()

        # 데이터베이스 오류 시뮬레이션
        mocker.patch.object(
            user_repository,
            "_create_user",
            side_effect=IntegrityError(None, None, None),
        )

        with pytest.raises(DatabaseError) as exc_info:
            user_repository.create_user(**data)

        assert str(exc_info.value) == "An error occurred while accessing the database"

    def test_valid_user_creation_schema(self):
        data = self.get_valid_data()
        user = UserCreate(**data)
        assert user.email == data["email"]
        assert user.password == data["password"]
        assert user.name == data["name"]

    def test_invalid_email_format_schema(self):
        data = self.get_valid_data()
        data["email"] = "invalid_email"
        with pytest.raises(ValidationError, match="value is not a valid email address"):
            UserCreate(**data)
