from app.schemas.base_schema import (
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
)

from pydantic import BaseModel


class DocumentCreate(CreateSchema, BaseModel):
    title: str


class DocumentUpdate(UpdateSchema, BaseModel):
    title: str


class DocumentResponse(ResponseSchema, BaseModel):
    title: str

    owner_id: int

    created_at: str
    updated_at: str

    is_deleted: bool
