from app.schemas.base_schema import CreateSchema, UpdateSchema, ResponseSchema
from datetime import datetime


class FeatureCreate(CreateSchema):
    title: str
    description: str | None
    project_id: int


class FeatureUpdate(UpdateSchema):
    title: str
    description: str | None


class FeatureResponse(ResponseSchema):
    id: int

    title: str
    description: str | None
    project_id: int

    owner_id: int

    created_at: datetime
    updated_at: datetime

    is_deleted: bool
