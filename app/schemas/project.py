import re
from typing import Any, Dict, Protocol

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils.validator import validate_field


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


class CreateSchema(Protocol):
    Create: type[BaseModel]


class UpdateSchema(Protocol):
    Update: type[BaseModel]


class ResponseSchema(Protocol):
    Response: type[BaseModel]


class BaseSchema(Protocol):
    Create: type[CreateSchema]
    Update: type[UpdateSchema]
    Response: type[ResponseSchema]


class ProjectCreate(ProjectBase, CreateSchema):
    title: str
    Create: type[BaseModel] = None  # This will be set to ProjectCreate itself

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.Create = cls


class ProjectUpdate(ProjectBase, UpdateSchema):
    Update: type[BaseModel] = None  # This will be set to ProjectUpdate itself

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.Update = cls

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_field(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values


class ProjectResponse(BaseModel, ResponseSchema):
    id: int
    title: str
    description: str | None = None
    founder_id: int
    Response: type[BaseModel] = None

    model_config = ConfigDict(from_attributes=True)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.Response = cls


class ProjectSchema(BaseSchema):
    Create = ProjectCreate
    Update = ProjectUpdate
    Response = ProjectResponse
