import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate


@pytest.mark.unit
@pytest.mark.req_1_basic_user_registration
class TestUserRegistrationValidation:
    @classmethod
    def setup_class(cls):
        cls.valid_data = {
            "email": "test@example.com",
            "password": "ValidPass1!",
            "name": "John Doe",
        }

    @classmethod
    def get_valid_data(cls):
        return cls.valid_data.copy()

    def test_valid_user_creation(self):
        user = UserCreate(**self.get_valid_data())
        assert user.email == self.valid_data["email"]
        assert user.password == self.valid_data["password"]
        assert user.name == self.valid_data["name"]

    def test_email_invalid_format(self):
        data = self.get_valid_data()
        data["email"] = "invalid_email"
        with pytest.raises(
            ValidationError, match="An email address must have an @-sign"
        ):
            UserCreate(**data)

    def test_email_too_long(self):
        data = self.get_valid_data()
        data["email"] = "a" * 90 + "@example.com"
        with pytest.raises(
            ValidationError, match="The email address is too long before the @-sign"
        ):
            UserCreate(**data)

    def test_password_too_short(self):
        data = self.get_valid_data()
        data["password"] = "Short1!"
        with pytest.raises(
            ValidationError, match="String should have at least 8 characters"
        ):
            UserCreate(**data)

    def test_password_too_long(self):
        data = self.get_valid_data()
        data["password"] = "A" * 21
        with pytest.raises(
            ValidationError, match="String should have at most 20 characters"
        ):
            UserCreate(**data)

    def test_password_no_lowercase(self):
        data = self.get_valid_data()
        data["password"] = "UPPERCASE1!"
        with pytest.raises(
            ValidationError, match="Password must include at least one lowercase letter"
        ):
            UserCreate(**data)

    def test_password_no_number(self):
        data = self.get_valid_data()
        data["password"] = "NoNumberPass!"
        with pytest.raises(
            ValidationError,
            match="Password must include at least one lowercase letter, one number, and one special character",
        ):
            UserCreate(**data)

    def test_password_no_special_char(self):
        data = self.get_valid_data()
        data["password"] = "NoSpecialChar1"
        with pytest.raises(
            ValidationError,
            match="Password must include at least one lowercase letter, one number, and one special character",
        ):
            UserCreate(**data)

    def test_name_valid_with_special_chars(self):
        data = self.get_valid_data()
        data["name"] = "Mary-Jane O'Connor"
        user = UserCreate(**data)
        assert user.name == "Mary-Jane O'Connor"

    def test_name_too_short(self):
        data = self.get_valid_data()
        data["name"] = "A"
        with pytest.raises(
            ValidationError, match="String should have at least 2 characters"
        ):
            UserCreate(**data)

    def test_name_too_long(self):
        data = self.get_valid_data()
        data["name"] = "A" * 51
        with pytest.raises(
            ValidationError, match="String should have at most 50 characters"
        ):
            UserCreate(**data)

    def test_name_invalid_char(self):
        data = self.get_valid_data()
        data["name"] = "John123"
        with pytest.raises(
            ValidationError,
            match="Name can only contain alphabets, spaces, hyphens, and apostrophes",
        ):
            UserCreate(**data)

    def test_email_whitespace_stripped(self):
        data = self.get_valid_data()
        data["email"] = " test@example.com "
        user = UserCreate(**data)
        assert user.email == "test@example.com"

    def test_password_whitespace_stripped(self):
        data = self.get_valid_data()
        data["password"] = " ValidPass1! "
        user = UserCreate(**data)
        assert user.password == "ValidPass1!"

    def test_name_whitespace_compressed(self):
        data = self.get_valid_data()
        data["name"] = "John   Doe"
        user = UserCreate(**data)
        assert user.name == "John Doe"
