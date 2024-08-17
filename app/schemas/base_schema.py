from typing import Protocol
from pydantic import BaseModel


class CreateSchema(BaseModel):
    Create: type[BaseModel]


class UpdateSchema(BaseModel):
    Update: type[BaseModel]


class ResponseSchema(BaseModel):
    Response: type[BaseModel]


class BaseSchema(Protocol):
    Create: type[CreateSchema]
    Update: type[UpdateSchema]
    Response: type[ResponseSchema]
