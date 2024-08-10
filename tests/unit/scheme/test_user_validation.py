import pytest
from pydantic import ValidationError
from app.schemas.users import UserCreate


@pytest.mark.req_1_basic_user_registration
class TestUserValidation:

    def test_valid_user_creation(self):
        user = UserCreate(
            email="test@example.com", password="ValidPass1!", name="John Doe"
        )
        assert user.email == "test@example.com"
        assert user.password == "ValidPass1!"
        assert user.name == "John Doe"

    def test_email_validation(self):
        # 유효한 이메일
        UserCreate(email="valid@example.com", password="ValidPass1!", name="John")

        # 유효하지 않은 이메일 형식
        with pytest.raises(ValidationError, match="Invalid email format"):
            UserCreate(email="invalid_email", password="ValidPass1!", name="John")

        # 허용되지 않는 특수문자
        with pytest.raises(
            ValidationError, match="Email contains disallowed special characters"
        ):
            UserCreate(
                email="invalid*@example.com", password="ValidPass1!", name="John"
            )

        # 이메일 길이 초과
        long_email = "a" * 90 + "@example.com"
        with pytest.raises(
            ValidationError, match="Email must not exceed 100 characters"
        ):
            UserCreate(email=long_email, password="ValidPass1!", name="John")

    def test_password_validation(self):
        # 유효한 비밀번호
        UserCreate(email="test@example.com", password="ValidPass1!", name="John")

        # 짧은 비밀번호
        with pytest.raises(
            ValidationError, match="ensure this value has at least 8 characters"
        ):
            UserCreate(email="test@example.com", password="Short1!", name="John")

        # 긴 비밀번호
        with pytest.raises(
            ValidationError, match="ensure this value has at most 20 characters"
        ):
            UserCreate(
                email="test@example.com", password="VeryLongPassword1234!", name="John"
            )

        # 복잡성 부족 (소문자 누락)
        with pytest.raises(
            ValidationError, match="Password must include at least one lowercase letter"
        ):
            UserCreate(email="test@example.com", password="UPPERCASE1!", name="John")

        # 복잡성 부족 (숫자 누락)
        with pytest.raises(
            ValidationError, match="Password must include at least one number"
        ):
            UserCreate(email="test@example.com", password="NoNumberPass!", name="John")

        # 복잡성 부족 (특수문자 누락)
        with pytest.raises(
            ValidationError,
            match="Password must include at least one special character",
        ):
            UserCreate(email="test@example.com", password="NoSpecialChar1", name="John")

    def test_name_validation(self):
        # 유효한 이름
        UserCreate(email="test@example.com", password="ValidPass1!", name="John Doe")
        UserCreate(
            email="test@example.com", password="ValidPass1!", name="Mary-Jane O'Connor"
        )

        # 짧은 이름
        with pytest.raises(
            ValidationError, match="ensure this value has at least 2 characters"
        ):
            UserCreate(email="test@example.com", password="ValidPass1!", name="A")

        # 긴 이름
        long_name = "A" * 51
        with pytest.raises(
            ValidationError, match="ensure this value has at most 50 characters"
        ):
            UserCreate(email="test@example.com", password="ValidPass1!", name=long_name)

        # 유효하지 않은 문자 포함
        with pytest.raises(
            ValidationError,
            match="Name can only contain alphabets, spaces, hyphens, and apostrophes",
        ):
            UserCreate(email="test@example.com", password="ValidPass1!", name="John123")

    def test_whitespace_handling(self):
        # 이메일 앞뒤 공백 제거
        user = UserCreate(
            email=" test@example.com ", password="ValidPass1!", name="John Doe"
        )
        assert user.email == "test@example.com"

        # 비밀번호 앞뒤 공백 제거
        user = UserCreate(
            email="test@example.com", password=" ValidPass1! ", name="John Doe"
        )
        assert user.password == "ValidPass1!"

        # 이름 중간 공백 압축
        user = UserCreate(
            email="test@example.com", password="ValidPass1!", name="John    Doe"
        )
        assert user
