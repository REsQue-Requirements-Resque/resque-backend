from typing import Generic, TypeVar, Type, List, Any
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.models.base_model import BaseModel
from app.repositories.base_repository import BaseRepository
from app.schemas.base_schema import BaseSchema

ModelType = TypeVar("ModelType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseSchema)


class BaseService(Generic[ModelType, SchemaType]):
    def __init__(self, repository: BaseRepository[ModelType], schema: Type[SchemaType]):
        self.repository = repository
        self.schema = schema

    async def create(
        self, obj_in: SchemaType.CreateSchema
    ) -> SchemaType.ResponseSchema:
        try:
            obj_dict = obj_in.model_dump()
            db_obj = await self.repository.create(obj_dict)
            return self.schema.ResponseSchema.model_validate(db_obj)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get(self, id: Any) -> SchemaType.ResponseSchema:
        obj = await self.repository.get(id)
        if not obj:
            raise HTTPException(status_code=404, detail="Object not found")
        return self.schema.ResponseSchema.model_validate(obj)

    async def update(
        self, id: Any, obj_in: SchemaType.UpdateSchema
    ) -> SchemaType.ResponseSchema:
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        updated_obj = await self.repository.update(id, update_data)
        if not updated_obj:
            raise HTTPException(
                status_code=404, detail="Object not found or update failed"
            )
        return self.schema.ResponseSchema.model_validate(updated_obj)

    async def delete(self, id: Any) -> bool:
        deleted = await self.repository.delete(id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Object not found or delete failed"
            )
        return True

    async def list(self) -> List[SchemaType.ResponseSchema]:
        try:
            objs = await self.repository.list()
            return [self.schema.ResponseSchema.model_validate(obj) for obj in objs]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
