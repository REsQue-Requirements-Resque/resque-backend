import pytest
from sqlalchemy import select
from app.models import User
from app.core.security import get_password_hash, verify_password
from app.services.authentication_service import AuthenticationService
from app.exceptions.user_exceptions import InvalidCredentialsError, TooManyAttemptsError
from app.schemas.user import UserLogin


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.req_2_user_login
class TestUserAuthentication:
    @pytest.fixture(autouse=True)
    async def setup(self, db_session):
        self.db_session = db_session
        self.auth_service = AuthenticationService(db_session)

        # Create a test user
        test_user = User(
            email="test@example.com",
            name="Test User",
            hashed_password=get_password_hash("correctPassword123!"),
        )
        self.db_session.add(test_user)
        await self.db_session.commit()

        yield

        # Clean up
        await self.db_session.execute(
            select(User).where(User.email == "test@example.com")
        )
        await self.db_session.commit()

    async def test_successful_login(self):
        user_login = UserLogin(email="test@example.com", password="correctPassword123!")
        user = await self.auth_service.authenticate_user(
            user_login.email, user_login.password
        )
        assert user is not None
        assert user.email == "test@example.com"

    async def test_failed_login_wrong_password(self):
        user_login = UserLogin(email="test@example.com", password="wrongPassword123!")
        with pytest.raises(InvalidCredentialsError):
            await self.auth_service.authenticate_user(
                user_login.email, user_login.password
            )

    async def test_failed_login_non_existent_user(self):
        user_login = UserLogin(
            email="nonexistent@example.com", password="somePassword123!"
        )
        with pytest.raises(InvalidCredentialsError):
            await self.auth_service.authenticate_user(
                user_login.email, user_login.password
            )

    async def test_login_attempt_limit(self, mocker):
        mocker.patch.object(
            AuthenticationService, "check_login_attempts", return_value=False
        )
        user_login = UserLogin(email="test@example.com", password="correctPassword123!")
        with pytest.raises(TooManyAttemptsError):
            await self.auth_service.authenticate_user(
                user_login.email, user_login.password
            )

    @pytest.mark.parametrize(
        "email,password,expected_error",
        [
            ("", "somePassword123!", InvalidCredentialsError),
            ("test@example.com", "", InvalidCredentialsError),
            ("not_an_email", "short", InvalidCredentialsError),
        ],
    )
    async def test_login_input_validation(self, email, password, expected_error):
        with pytest.raises(expected_error):
            user_login = UserLogin(email=email, password=password)
            await self.auth_service.authenticate_user(
                user_login.email, user_login.password
            )

    async def test_password_hashing_and_verification(self):
        password = "testPassword123!"
        hashed_password = get_password_hash(password)
        assert verify_password(password, hashed_password)
        assert not verify_password("wrongPassword", hashed_password)

    async def test_user_retrieval(self):
        user = await self.auth_service.get_user_by_email("test@example.com")
        assert user is not None
        assert user.email == "test@example.com"

        non_existent_user = await self.auth_service.get_user_by_email(
            "nonexistent@example.com"
        )
        assert non_existent_user is None
