import pytest
from app.schemas.users import UserCreate
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.exceptions.user_exceptions import DuplicateEmailError, DatabaseError


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
    def setup(self, db_session):
        self.user_repository = UserRepository(db_session)
        existing_user = User(
            email=self.emails["existing"],
            password=self.passwords["valid"],
            name=self.names["valid"],
        )
        db_session.add(existing_user)
        db_session.commit()

    def test_register_user_with_unique_email(self):
        data = self.get_valid_data()
        user = self.user_repository.create_user(UserCreate(**data))

        assert user is not None
        assert user.email == data["email"]
        assert self.user_repository.get_user_by_email(data["email"]) is not None

    def test_register_user_with_duplicate_email(self):
        data = self.get_valid_data()
        data["email"] = self.emails["existing"]

        with pytest.raises(DuplicateEmailError) as exc_info:
            self.user_repository.create_user(UserCreate(**data))

        assert str(exc_info.value) == "Email already exists"

    def test_register_user_with_case_insensitive_duplicate_email(self):
        data = self.get_valid_data()
        data["email"] = self.emails["case_insensitive"]

        with pytest.raises(DuplicateEmailError) as exc_info:
            self.user_repository.create_user(UserCreate(**data))

        assert str(exc_info.value) == "Email already exists"

    def test_database_error_during_user_creation(self, mocker):
        data = self.get_valid_data()

        # Mock the database session to raise an exception
        mocker.patch.object(
            self.user_repository,
            "_create_user",
            side_effect=Exception("Database error"),
        )

        with pytest.raises(DatabaseError) as exc_info:
            self.user_repository.create_user(UserCreate(**data))

        assert str(exc_info.value) == "An error occurred while accessing the database"
