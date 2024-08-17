from typing import Any, Dict, List, Optional, TypeVar, Generic
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, db_session: AsyncSession, model: T):
        self.db_session = db_session
        self.model: BaseModel = model

    async def create(self, data: Dict[str, Any]) -> T:
        try:
            db_obj = self.model(**data)
            self.db_session.add(db_obj)
            await self.db_session.commit()
            await self.db_session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise e

    async def get(self, id: Any) -> Optional[T]:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> List[T]:
        stmt = select(self.model)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[T]:
        try:
            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(**data)
                .returning(self.model)
            )
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise e

    async def delete(self, id: Any) -> bool:
        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise e
