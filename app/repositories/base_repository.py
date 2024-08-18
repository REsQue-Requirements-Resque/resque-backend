"""
이 모듈은 SQLAlchemy와 함께 사용되는 기본 저장소 클래스를 정의합니다.
이 클래스는 일반적인 데이터베이스 CRUD 작업을 추상화하여 제공합니다.
"""

from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base_model import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    모든 저장소 클래스의 기본이 되는 베이스 저장소 클래스입니다.
    기본적인 CRUD 작업을 제공합니다.
    """

    def __init__(self, db_session: AsyncSession, model: Type[ModelType]):
        """
        BaseRepository 클래스의 생성자입니다.

        :param db_session: 데이터베이스 세션
        :param model: 이 저장소가 다루는 모델 클래스
        """
        self.db_session = db_session
        self.model = model

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        새로운 모델 인스턴스를 생성합니다.

        :param obj_in: 생성할 객체의 데이터
        :return: 생성된 모델 인스턴스
        """
        db_obj = self.model(**obj_in)
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        return db_obj

    async def get(self, id: Any) -> Optional[ModelType]:
        """
        ID로 모델 인스턴스를 조회합니다.

        :param id: 조회할 객체의 ID
        :return: 조회된 모델 인스턴스 또는 None
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> List[ModelType]:
        """
        모든 모델 인스턴스를 조회합니다.

        :return: 조회된 모든 모델 인스턴스 리스트
        """
        stmt = select(self.model)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """
        모델 인스턴스를 업데이트합니다.

        :param db_obj: 업데이트할 데이터베이스 객체
        :param obj_in: 업데이트할 데이터
        :return: 업데이트된 모델 인스턴스
        """
        for field in obj_in:
            setattr(db_obj, field, obj_in[field])
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        return db_obj

    async def delete(self, id: Any) -> Optional[ModelType]:
        """
        ID로 모델 인스턴스를 삭제합니다.

        :param id: 삭제할 객체의 ID
        :return: 삭제된 모델 인스턴스 또는 None
        """
        obj = await self.get(id)
        if obj:
            await self.db_session.delete(obj)
            await self.db_session.commit()
        return obj
