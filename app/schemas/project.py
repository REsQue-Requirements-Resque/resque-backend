from pydantic import BaseModel, field_validator, Field
from app.utils.validator import validate_field
import re


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    founder_id: int = Field(..., strict=True)

    @field_validator("title")
    def validate_title(cls, value: str) -> str:
        return validate_field(
            [cls.title_characters, cls.check_title_length], value.strip()
        )

    @staticmethod
    def title_characters(s: str) -> str:
        if not re.match(r"^[a-zA-Z0-9\s]+$", s):
            raise ValueError(
                "Project title must contain only English characters and numbers"
            )
        return s

    @staticmethod
    def check_title_length(value: str) -> str:
        if len(value) < 3 or len(value) > 100:
            raise ValueError("Project title must be between 3 and 100 characters")
        return value

    @field_validator("description")
    def validate_description(cls, value: str | None) -> str | None:
        if value:
            return validate_field(
                [lambda x: x.strip(), cls.check_description_length], value
            )
        return value

    @staticmethod
    def check_description_length(value: str | None) -> str | None:
        if value and len(value) > 1000:
            raise ValueError("Project description must not exceed 1000 characters")
        return value

    @field_validator("founder_id")
    def validate_founder_id(cls, value: int) -> int:
        return cls.check_positive_founder_id(value)

    @staticmethod
    def check_positive_founder_id(value: int) -> int:
        if value <= 0:
            raise ValueError("Founder ID must be a positive integer")
        return value


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
