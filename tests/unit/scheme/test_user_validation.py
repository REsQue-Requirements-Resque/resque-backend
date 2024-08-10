import pytest
from pydantic import ValidationError
from app.schemas.users import UserCreate


@pytest.mark.req_1_basic_user_registration
class TestUserValidation:
    @classmethod
    def setup_class(cls):
        cls.emails = {
            "valid": "test@example.com",
            "invalid_format": "invalid_email",
            "invalid_special_char": "invalid*@example.com",
            "too_long": "a" * 90 + "@example.com",
        }
        cls.passwords = {
            "valid": "ValidPass1!",
            "too_short": "Short1!",
            "too_long": "A" * 21,
            "no_lowercase": "UPPERCASE1!",
            "no_number": "NoNumberPass!",
            "no_special_char": "NoSpecialChar1",
        }
        cls.names = {
            "valid": "John Doe",
            "valid_with_special": "Mary-Jane O'Connor",
            "too_short": "A",
            "too_long": "A" * 51,
            "invalid_char": "John123",
        }

    @classmethod
    def get_valid_data(cls):
        return {
            "email": cls.emails["valid"],
            "password": cls.passwords["valid"],
            "name": cls.names["valid"],
        }

    def test_valid_user_creation(self):
        data = self.get_valid_data()
        user = UserCreate(**data)
        assert user.email == data["email"]
        assert user.password == data["password"]
        assert user.name == data["name"]

    def test_email_invalid_format(self):
        data = self.get_valid_data()
        data["email"] = self.emails["invalid_format"]
        with pytest.raises(
            ValidationError, match="An email address must have an @-sign"
        ):
            UserCreate(**data)

    def test_email_too_long(self):
        data = self.get_valid_data()
        data["email"] = self.emails["too_long"]
        with pytest.raises(
            ValidationError, match="The email address is too long before the @-sign"
        ):
            UserCreate(**data)

    def test_password_too_short(self):
        data = self.get_valid_data()
        data["password"] = self.passwords["too_short"]
        with pytest.raises(
            ValidationError, match="String should have at least 8 characters"
        ):
            UserCreate(**data)

    def test_password_too_long(self):
        data = self.get_valid_data()
        data["password"] = self.passwords["too_long"]
        with pytest.raises(
            ValidationError, match="String should have at most 20 characters"
        ):
            UserCreate(**data)

    def test_password_no_lowercase(self):
        data = self.get_valid_data()
        data["password"] = self.passwords["no_lowercase"]
        with pytest.raises(
            ValidationError, match="Password must include at least one lowercase letter"
        ):
            UserCreate(**data)

    def test_password_no_number(self):
        data = self.get_valid_data()
        data["password"] = self.passwords["no_number"]
        with pytest.raises(
            ValidationError,
            match="Password must include at least one lowercase letter, one number, and one special character",
        ):
            UserCreate(**data)

    def test_password_no_special_char(self):
        data = self.get_valid_data()
        data["password"] = self.passwords["no_special_char"]
        with pytest.raises(
            ValidationError,
            match="Password must include at least one lowercase letter, one number, and one special character",
        ):
            UserCreate(**data)

    def test_name_valid_with_special_chars(self):
        data = self.get_valid_data()
        data["name"] = self.names["valid_with_special"]
        user = UserCreate(**data)
        assert user.name == self.names["valid_with_special"]

    def test_name_too_short(self):
        data = self.get_valid_data()
        data["name"] = self.names["too_short"]
        with pytest.raises(
            ValidationError, match="String should have at least 2 characters"
        ):
            UserCreate(**data)

    def test_name_too_long(self):
        data = self.get_valid_data()
        data["name"] = self.names["too_long"]
        with pytest.raises(
            ValidationError, match="String should have at most 50 characters"
        ):
            UserCreate(**data)

    def test_name_invalid_char(self):
        data = self.get_valid_data()
        data["name"] = self.names["invalid_char"]
        with pytest.raises(
            ValidationError,
            match="Name can only contain alphabets, spaces, hyphens, and apostrophes",
        ):
            UserCreate(**data)

    def test_email_whitespace_stripped(self):
        data = self.get_valid_data()
        data["email"] = f" {data['email']} "
        user = UserCreate(**data)
        assert user.email == self.emails["valid"]

    def test_password_whitespace_stripped(self):
        data = self.get_valid_data()
        data["password"] = f" {data['password']} "
        user = UserCreate(**data)
        assert user.password == self.passwords["valid"]

    def test_name_whitespace_compressed(self):
        data = self.get_valid_data()
        data["name"] = "John    Doe"
        user = UserCreate(**data)
        assert user.name == "John Doe"
