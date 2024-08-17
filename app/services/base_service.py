from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

from app.repositories.base_repository import BaseRepository

T = TypeVar("T")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[T, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    async def create(self, obj_in: CreateSchemaType) -> T:
        try:
            obj_dict = obj_in.model_dump()
            return await self.repository.create(obj_dict)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get(self, id: Any) -> T:
        obj = await self.repository.get(id)
        if not obj:
            raise HTTPException(status_code=404, detail="Object not found")
        return obj

    async def update(self, id: Any, obj_in: UpdateSchemaType) -> T:
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        updated_obj = await self.repository.update(id, update_data)
        if not updated_obj:
            raise HTTPException(
                status_code=404, detail="Object not found or update failed"
            )
        return updated_obj

    async def delete(self, id: Any) -> bool:
        deleted = await self.repository.delete(id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Object not found or delete failed"
            )
        return True

    async def list(self) -> List[T]:
        try:
            return await self.repository.list()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
