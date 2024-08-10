import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.utils.validator import validate_field


class UserCreate(BaseModel):
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=20)
    name: str = Field(..., min_length=2, max_length=50)

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        return validate_field(
            [lambda x: x.strip(), cls.password_complexity], value  # 공백 제거
        )

    @staticmethod
    def password_complexity(value: str) -> str:
        if not (
            any(c.islower() for c in value)
            and any(c.isdigit() for c in value)
            and any(c in "!@#$%^&*()_+" for c in value)
        ):
            raise ValueError(
                "Password must include at least one lowercase letter, one number, and one special character"
            )
        return value

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        return validate_field(
            [cls.name_characters, lambda x: " ".join(x.split())],
            value,  # 중간 공백 압축
        )

    @staticmethod
    def name_characters(value: str) -> str:
        if not re.match(r"^[a-zA-Z\s\'-]+$", value):
            raise ValueError(
                "Name can only contain alphabets, spaces, hyphens, and apostrophes"
            )
        return value
