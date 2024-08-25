from typing import Type, List, Optional, Any, Dict, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base_model import BaseModel
from sqlalchemy.sql.expression import update
from sqlalchemy.exc import SQLAlchemyError

T = TypeVar("T", bound=BaseModel)


class BaseRepository:
    _model_class: Type[T] = None

    def __init__(self, db_session: AsyncSession):
        if self._model_class is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must declare _model_class"
            )
        self.db_session = db_session

    async def create(self, obj_in: Dict[str, Any]) -> T:
        try:
            db_obj = self._model_class(**obj_in)
            self.db_session.add(db_obj)
            await self.db_session.commit()
            await self.db_session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise

    async def list(self) -> List[T]:
        stmt = select(self._model_class)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[T]:
        try:
            stmt = (
                update(self._model_class)
                .where(self._model_class.id == id)
                .values(**obj_in)
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            return await self.get(id)  # 업데이트된 객체를 다시 조회
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise

    async def get(self, id: Any) -> Optional[T]:
        stmt = select(self._model_class).where(self._model_class.id == id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, id: Any) -> Optional[T]:
        try:
            obj = await self.get(id)
            if obj:
                await self.db_session.delete(obj)
                await self.db_session.commit()
            return obj
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise
