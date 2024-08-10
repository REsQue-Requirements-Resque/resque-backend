import pytest
from sqlalchemy.orm import Session
from app.schemas.users import UserCreate
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, get_password_hash
from app.exceptions.user_exceptions import DuplicateEmailError, DatabaseError


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
    def setup(self, db_session):
        self.user_repository = UserRepository(db_session)
        existing_user = User(
            email=self.emails["existing"],
            name=self.names["valid"],
            hashed_password=get_password_hash(self.passwords["valid"]),
        )
        db_session.add(existing_user)
        db_session.flush()

    def test_password_hashing(self, db_session: Session):
        user_data = self.get_valid_data()
        user_create = UserCreate(**user_data)
        created_user = self.user_repository.create_user(user_create)

        assert created_user.hashed_password != user_data["password"]
        assert created_user.hashed_password != get_password_hash(user_data["password"])

    def test_hashed_password_verification(self, db_session: Session):
        user_data = self.get_valid_data()
        user_create = UserCreate(**user_data)
        created_user = self.user_repository.create_user(user_create)

        assert verify_password(user_data["password"], created_user.hashed_password)

    def test_password_not_stored_in_plaintext(self, db_session: Session):
        user_data = self.get_valid_data()
        user_data["email"] = "another@example.com"
        user_create = UserCreate(**user_data)
        created_user = self.user_repository.create_user(user_create)

        stored_user = db_session.query(User).filter_by(email=user_data["email"]).first()
        assert user_data["password"] not in stored_user.hashed_password
        assert get_password_hash(user_data["password"]) != stored_user.hashed_password
