import pytest
from fastapi import HTTPException
from jose import jwt
from datetime import datetime, timedelta, UTC
from app.services.authentication_service import AuthenticationService
from app.core.config import settings
from app.schemas.token import TokenData


@pytest.fixture
def mock_user_repository(mocker):
    return mocker.AsyncMock()


@pytest.fixture
def auth_service(mock_user_repository):
    return AuthenticationService(mock_user_repository)


def create_token(username: str, expires_delta: timedelta = None):
    to_encode = {"sub": username}
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


class TestAuthenticationService:

    def test_decode_token_valid(self, auth_service):
        username = "testuser"
        token = create_token(username)
        result = auth_service.decode_token(token)
        assert isinstance(result, TokenData)
        assert result.username == username

    def test_decode_token_expired(self, auth_service):
        token = create_token("testuser", expires_delta=timedelta(minutes=-1))
        with pytest.raises(ValueError, match="Invalid token"):
            auth_service.decode_token(token)

    def test_decode_token_invalid(self, auth_service):
        with pytest.raises(ValueError, match="Invalid token"):
            auth_service.decode_token("invalid_token")

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_service, mock_user_repository):
        username = "testuser"
        token = create_token(username)
        mock_user = {"username": username}
        mock_user_repository.get_by_username.return_value = mock_user

        result = await auth_service.get_current_user(token)
        assert result == mock_user
        mock_user_repository.get_by_username.assert_called_once_with(username)

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(
        self, auth_service, mock_user_repository
    ):
        username = "testuser"
        token = create_token(username)
        mock_user_repository.get_by_username.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user(token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_get_user_success(self, auth_service, mock_user_repository):
        username = "testuser"
        mock_user = {"username": username}
        mock_user_repository.get_by_username.return_value = mock_user

        result = await auth_service.get_user(username)
        assert result == mock_user
        mock_user_repository.get_by_username.assert_called_once_with(username)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, auth_service, mock_user_repository):
        username = "testuser"
        mock_user_repository.get_by_username.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_user(username)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == f"User with username {username} not found"

    @pytest.mark.asyncio
    async def test_get_user_exception(self, auth_service, mock_user_repository):
        username = "testuser"
        mock_user_repository.get_by_username.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_user(username)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "An error occurred while retrieving the user"
