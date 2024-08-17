from typing import Generic, TypeVar, Type
from pydantic import BaseModel


class CreateSchema(BaseModel):
    """Base class for create operation schemas."""


class UpdateSchema(BaseModel):
    """Base class for update operation schemas."""


class ResponseSchema(BaseModel):
    """Base class for response schemas."""


CreateSchemaType = TypeVar("CreateSchemaType", bound=CreateSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=UpdateSchema)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=ResponseSchema)


class BaseSchema(Generic[CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """
    A generic base schema class that encapsulates create, update, and response schemas.

    Type Parameters:
    - CreateSchemaType: The type of the create schema, must be a subclass of CreateSchema.
    - UpdateSchemaType: The type of the update schema, must be a subclass of UpdateSchema.
    - ResponseSchemaType: The type of the response schema, must be a subclass of ResponseSchema.
    """

    CreateSchema: Type[CreateSchemaType]
    UpdateSchema: Type[UpdateSchemaType]
    ResponseSchema: Type[ResponseSchemaType]
