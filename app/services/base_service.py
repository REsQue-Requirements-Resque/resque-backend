from typing import List, Any, Optional, Type
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.models.base_model import BaseModel
from app.repositories.base_repository import BaseRepository
from app.schemas.base_schema import (
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
    PaginatedResponse,
)


class BaseService:
    """기본 서비스 클래스입니다.

    이 클래스는 Repository 패턴을 사용하여 CRUD 작업을 수행합니다.
    각 구체적인 서비스는 이 클래스를 상속받아 구현해야 합니다.

    Attributes:
        repository (BaseRepository): 사용할 리포지토리 인스턴스입니다.
        model (Type[BaseModel]): 이 서비스가 다루는 모델 클래스입니다.
        create_schema (Type[CreateSchema]): 객체 생성에 사용할 스키마 클래스입니다.
        update_schema (Type[UpdateSchema]): 객체 업데이트에 사용할 스키마 클래스입니다.
        response_schema (Type[ResponseSchema]): 응답에 사용할 스키마 클래스입니다.
    """

    repository: BaseRepository
    model: Type[BaseModel]
    create_schema: Type[CreateSchema]
    update_schema: Type[UpdateSchema]
    response_schema: Type[ResponseSchema]

    def __init__(self, repository: BaseRepository):
        """BaseService 클래스의 생성자입니다.

        Args:
            repository (BaseRepository): 사용할 리포지토리 인스턴스입니다.
        """
        self.repository = repository

    async def create(self, obj_in: CreateSchema) -> ResponseSchema:
        """새로운 객체를 생성합니다.

        Args:
            obj_in (CreateSchema): 생성할 객체의 데이터입니다.

        Returns:
            ResponseSchema: 생성된 객체의 데이터입니다.

        Raises:
            HTTPException: 데이터베이스 오류가 발생한 경우 발생합니다.
        """
        try:
            obj_dict = obj_in.model_dump()
            db_obj = await self.repository.create(obj_dict)
            return self.response_schema.model_validate(db_obj)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get(self, id: Any) -> ResponseSchema:
        """ID로 객체를 조회합니다.

        Args:
            id (Any): 조회할 객체의 ID입니다.

        Returns:
            ResponseSchema: 조회된 객체의 데이터입니다.

        Raises:
            HTTPException: 객체를 찾을 수 없거나 데이터베이스 오류가 발생한 경우 발생합니다.
        """
        try:
            db_obj = await self.repository.get(id)
            if not db_obj:
                raise HTTPException(status_code=404, detail="Object not found")
            return self.response_schema.model_validate(db_obj)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def list(self, skip: int = 0, limit: int = 100) -> PaginatedResponse:
        """객체 목록을 조회합니다.

        Args:
            skip (int): 건너뛸 객체의 수입니다. 기본값은 0입니다.
            limit (int): 조회할 최대 객체의 수입니다. 기본값은 100입니다.

        Returns:
            PaginatedResponse: 페이지네이션된 객체 목록입니다.

        Raises:
            HTTPException: 데이터베이스 오류가 발생한 경우 발생합니다.
        """
        try:
            db_objs = await self.repository.list()
            total = len(db_objs)
            items = [
                self.response_schema.model_validate(obj)
                for obj in db_objs[skip : skip + limit]
            ]
            return PaginatedResponse(
                items=items, total=total, page=skip // limit + 1, size=limit
            )
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update(self, id: Any, obj_in: UpdateSchema) -> ResponseSchema:
        """객체를 업데이트합니다.

        Args:
            id (Any): 업데이트할 객체의 ID입니다.
            obj_in (UpdateSchema): 업데이트할 데이터입니다.

        Returns:
            ResponseSchema: 업데이트된 객체의 데이터입니다.

        Raises:
            HTTPException: 객체를 찾을 수 없거나 데이터베이스 오류가 발생한 경우 발생합니다.
        """
        try:
            db_obj = await self.repository.get(id)
            if not db_obj:
                raise HTTPException(status_code=404, detail="Object not found")
            update_data = obj_in.model_dump(exclude_unset=True)
            updated_obj = await self.repository.update(id, update_data)
            return self.response_schema.model_validate(updated_obj)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def delete(self, id: Any) -> Optional[ResponseSchema]:
        """객체를 삭제합니다.

        Args:
            id (Any): 삭제할 객체의 ID입니다.

        Returns:
            Optional[ResponseSchema]: 삭제된 객체의 데이터입니다. 객체가 존재하지 않으면 None을 반환합니다.

        Raises:
            HTTPException: 데이터베이스 오류가 발생한 경우 발생합니다.
        """
        try:
            db_obj = await self.repository.delete(id)
            if not db_obj:
                raise HTTPException(status_code=404, detail="Object not found")
            return self.response_schema.model_validate(db_obj)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
