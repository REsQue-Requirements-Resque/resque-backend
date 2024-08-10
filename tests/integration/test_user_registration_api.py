import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.core.security import verify_password


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.req_1_basic_user_registration
class TestUserRegistrationAPI:
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):

        db_session.query(User).delete()
        db_session.commit()

    def test_register_user_success(self, client: TestClient, db_session: Session):
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User",
        }
        response = client.post("/api/users/register", json=user_data)

        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["email"] == user_data["email"]
        assert response.json()["name"] == user_data["name"]
        assert "password" not in response.json()

        # 데이터베이스에 사용자가 생성되었는지 확인
        db_user = (
            db_session.query(User).filter(User.email == user_data["email"]).first()
        )
        assert db_user is not None
        assert db_user.email == user_data["email"]
        assert db_user.name == user_data["name"]
        assert verify_password(user_data["password"], db_user.hashed_password)

    def test_register_user_duplicate_email(
        self, client: TestClient, db_session: Session
    ):
        user_data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "name": "Existing User",
        }
        # 먼저 사용자 생성
        client.post("/api/users/register", json=user_data)

        # 같은 이메일로 다시 생성 시도
        response = client.post("/api/users/register", json=user_data)

        assert response.status_code == 400
        assert "email already exists" in response.json()["detail"].lower()

    def test_register_user_invalid_data(self, client: TestClient):
        invalid_data = {"email": "invalid-email", "password": "short", "name": ""}
        response = client.post("/api/users/register", json=invalid_data)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("email" in error["msg"].lower() for error in errors)
        assert any("password" in error["msg"].lower() for error in errors)
        assert any("name" in error["msg"].lower() for error in errors)

    def test_register_user_missing_data(self, client: TestClient):
        incomplete_data = {"email": "incomplete@example.com"}
        response = client.post("/api/users/register", json=incomplete_data)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("password" in error["msg"].lower() for error in errors)
        assert any("name" in error["msg"].lower() for error in errors)

    @pytest.mark.parametrize(
        "invalid_password",
        [
            "short",  # 너무 짧은 비밀번호
            "onlylowercase",  # 대문자 없음
            "ONLYUPPERCASE",  # 소문자 없음
            "NoSpecialChar1",  # 특수문자 없음
            "NoNumber!",  # 숫자 없음
        ],
    )
    def test_register_user_invalid_password(self, client: TestClient, invalid_password):
        user_data = {
            "email": "testuser@example.com",
            "password": invalid_password,
            "name": "Test User",
        }
        response = client.post("/api/users/register", json=user_data)

        assert response.status_code == 422
        assert "password" in response.json()["detail"][0]["msg"].lower()
