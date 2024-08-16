from pydantic import BaseModel, field_validator, ConfigDict, Field, model_validator
from app.utils.validator import validate_field
import re
from typing import Dict, Any


class ProjectBase(BaseModel):
    title: str | None = None
    description: str | None = None

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

    @staticmethod
    def check_description_length(value: str | None) -> str | None:
        if value and len(value) > 1000:
            raise ValueError("Project description must not exceed 1000 characters")
        return value

    @field_validator("title")
    def validate_title(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_field(
                [cls.title_characters, cls.check_title_length], value.strip()
            )
        return value

    @field_validator("description")
    def validate_description(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_field(
                [lambda x: x.strip(), cls.check_description_length], value
            )
        return value


class ProjectCreate(ProjectBase):
    title: str


class ProjectUpdate(ProjectBase):
    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_field(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    founder_id: int

    model_config = ConfigDict(from_attributes=True)
