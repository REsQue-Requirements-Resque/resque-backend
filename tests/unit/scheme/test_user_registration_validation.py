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
    @classmethod
    def setup_class(cls):
        cls.endpoints = {"register": "/api/users/register"}
        cls.valid_user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User",
        }
        cls.invalid_data = {
            "email": {
                "invalid_format": "invalid-email",
                "too_long": "a" * 90 + "@example.com",
            },
            "password": {
                "too_short": "Short1!",
                "no_uppercase": "lowercase123!",
                "no_lowercase": "UPPERCASE123!",
                "no_number": "NoNumberPass!",
                "no_special_char": "NoSpecialChar1",
            },
            "name": {
                "too_short": "A",
                "too_long": "A" * 51,
                "invalid_char": "John123",
            },
        }

    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        db_session.query(User).delete()
        db_session.commit()

    def test_register_user_success(self, client: TestClient, db_session: Session):
        response = client.post(self.endpoints["register"], json=self.valid_user_data)

        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["email"] == self.valid_user_data["email"]
        assert response.json()["name"] == self.valid_user_data["name"]
        assert "password" not in response.json()

        db_user = (
            db_session.query(User)
            .filter(User.email == self.valid_user_data["email"])
            .first()
        )
        assert db_user is not None
        assert db_user.email == self.valid_user_data["email"]
        assert db_user.name == self.valid_user_data["name"]
        assert verify_password(
            self.valid_user_data["password"], db_user.hashed_password
        )

    def test_register_user_duplicate_email(self, client: TestClient):
        # 먼저 사용자 생성
        client.post(self.endpoints["register"], json=self.valid_user_data)

        # 같은 이메일로 다시 생성 시도
        response = client.post(self.endpoints["register"], json=self.valid_user_data)

        assert response.status_code == 400
        assert "email already exists" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "field,invalid_value",
        [
            ("email", "invalid_format"),
            ("password", "too_short"),
            ("name", ""),
        ],
    )
    def test_register_user_invalid_data(self, client: TestClient, field, invalid_value):
        invalid_data = self.valid_user_data.copy()
        invalid_data[field] = self.invalid_data[field].get(invalid_value, invalid_value)
        response = client.post(self.endpoints["register"], json=invalid_data)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(field in error["msg"].lower() for error in errors)

    def test_register_user_missing_data(self, client: TestClient):
        incomplete_data = {"email": self.valid_user_data["email"]}
        response = client.post(self.endpoints["register"], json=incomplete_data)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("password" in error["msg"].lower() for error in errors)
        assert any("name" in error["msg"].lower() for error in errors)

    @pytest.mark.parametrize(
        "invalid_password",
        [
            "too_short",
            "no_uppercase",
            "no_lowercase",
            "no_number",
            "no_special_char",
        ],
    )
    def test_register_user_invalid_password(self, client: TestClient, invalid_password):
        invalid_data = self.valid_user_data.copy()
        invalid_data["password"] = self.invalid_data["password"][invalid_password]
        response = client.post(self.endpoints["register"], json=invalid_data)

        assert response.status_code == 422
        assert "password" in response.json()["detail"][0]["msg"].lower()
