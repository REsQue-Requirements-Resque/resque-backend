from typing import Optional, List
from pydantic import BaseModel
from app.schemas.base_schema import CreateSchema, UpdateSchema, ResponseSchema
from app.utils.enums import PriorityEnum


class RequirementCreate(CreateSchema, BaseModel):
    title: str
    description: Optional[str] = None
    priority: PriorityEnum
    feature_id: int


class RequirementUpdate(UpdateSchema, BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    feature_id: Optional[int] = None


class RequirementResponse(ResponseSchema, BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    priority: PriorityEnum
    feature_id: int

    owner_id: int
    created_at: str
    updated_at: str
    is_deleted: bool
