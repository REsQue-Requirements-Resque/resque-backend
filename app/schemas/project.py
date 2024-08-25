from typing import Any, Dict
from app.schemas.base_schema import (
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
)
from pydantic import BaseModel


class ProjectCreate(CreateSchema, BaseModel):
    title: str
    description: str | None


class ProjectUpdate(UpdateSchema, BaseModel):
    title: str
    description: str | None


class ProjectResponse(ResponseSchema, BaseModel):
    title: str
    description: str | None

    owner_id: int

    created_at: str
    updated_at: str

    is_deleted: bool
