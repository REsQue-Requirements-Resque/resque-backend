import pytest
from pydantic import ValidationError
from app.schemas.user import UserLogin

@pytest.mark.unit
class TestUserLoginValidation:
    @classmethod
    def setup_class(cls):
        cls.valid_data = {
            "email": "test@example.com",
            "password": "ValidPass1!",
        }

    @classmethod
    def get_valid_data(cls):
        return cls.valid_data.copy()

    def test_valid_user_login(self):
        user_login = UserLogin(**self.get_valid_data())
        assert user_login.email == self.valid_data["email"]
        assert user_login.password == self.valid_data["password"]

    def test_email_invalid_format(self):
        data = self.get_valid_data()
        data["email"] = "invalid_email"
        with pytest.raises(ValidationError, match="value is not a valid email address"):
            UserLogin(**data)

    def test_email_too_long(self):
        data = self.get_valid_data()
        data["email"] = "a" * 90 + "@example.com"
        with pytest.raises(ValidationError):
            UserLogin(**data)

    def test_password_too_short(self):
        data = self.get_valid_data()
        data["password"] = "Short1!"
        with pytest.raises(ValidationError):
            UserLogin(**data)

    def test_password_too_long(self):
        data = self.get_valid_data()
        data["password"] = "A" * 21
        with pytest.raises(ValidationError):
            UserLogin(**data)

    def test_email_field_empty(self):
        data = self.get_valid_data()
        data["email"] = ""
        with pytest.raises(ValidationError, match="value is not a valid email address"):
            UserLogin(**data)

    def test_password_field_empty(self):
        data = self.get_valid_data()
        data["password"] = ""
        with pytest.raises(ValidationError, match="String should have at least 8 characters"):
            UserLogin(**data)

    def test_email_whitespace_stripped(self):
        data = self.get_valid_data()
        data["email"] = " test@example.com "
        user_login = UserLogin(**data)
        assert user_login.email == "test@example.com"

    def test_password_whitespace_stripped(self):
        data = self.get_valid_data()
        data["password"] = " ValidPass1! "
        user_login = UserLogin(**data)
        assert user_login.password == "ValidPass1!"