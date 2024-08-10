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
            name=self.names["valid"],
            hashed_password="hashed_"
            + self.passwords["valid"],  # 실제로는 해싱 함수를 사용해야 합니다
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

    def test_database_error_during_user_creation(self, db_session):
        # 1. 유효한 사용자 데이터 준비
        user_data = self.get_valid_data()

        # 2. 데이터베이스 세션을 조작하여 OperationalError를 발생시킵니다.
        def mock_commit():
            raise DatabaseError("An error occurred while accessing the database")

        original_commit = db_session.commit
        db_session.commit = mock_commit

        # 3. 사용자 생성 시도 및 DatabaseError 확인
        with pytest.raises(DatabaseError) as exc_info:
            self.user_repository.create_user(UserCreate(**user_data))

        # 4. 오류 메시지 확인
        assert (
            str(exc_info.value)
            == "An unexpected error occurred: An error occurred while accessing the database"
        )

        # 5. 데이터베이스에 사용자가 생성되지 않았는지 확인
        assert (
            db_session.query(User).filter_by(email=user_data["email"]).first() is None
        )

        db_session.commit = original_commit
