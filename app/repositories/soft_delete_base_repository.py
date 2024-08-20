from typing import Type, List, Optional, Any, Dict, TypeVar
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base_model import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
from app.repositories.base_repository import BaseRepository

ST = TypeVar("ST", bound=SoftDeleteMixin)


class SoftDeleteBaseRepository(BaseRepository[ST]):
    """소프트 삭제 기능을 지원하는 기본 저장소 클래스입니다.

    이 클래스는 BaseRepository를 상속받아 소프트 삭제 기능을 추가합니다.
    SoftDeleteMixin을 상속받은 모델에 대해 작동합니다.

    Attributes:
        _model_class (Type[ST]): 이 저장소가 다루는 모델 클래스입니다.
    """

    _model_class: Type[ST] = None

    async def list(self) -> List[ST]:
        """삭제되지 않은 모든 모델 인스턴스를 조회합니다.

        Returns:
            List[ST]: 삭제되지 않은 모델 인스턴스들의 리스트입니다.
        """
        stmt = select(self._model_class).where(self._model_class.is_deleted == False)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, id: Any) -> Optional[ST]:
        """주어진 ID에 해당하는 삭제되지 않은 모델 인스턴스를 조회합니다.

        Args:
            id (Any): 조회할 모델 인스턴스의 ID입니다.

        Returns:
            Optional[ST]: 조회된 모델 인스턴스 또는 None (인스턴스가 없거나 삭제된 경우)입니다.
        """
        stmt = select(self._model_class).where(
            (self._model_class.id == id) & (self._model_class.is_deleted == False)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, id: Any) -> Optional[ST]:
        """주어진 ID에 해당하는 모델 인스턴스를 소프트 삭제합니다.

        Args:
            id (Any): 삭제할 모델 인스턴스의 ID입니다.

        Returns:
            Optional[ST]: 소프트 삭제된 모델 인스턴스 또는 None (인스턴스가 없는 경우)입니다.

        Raises:
            SQLAlchemyError: 데이터베이스 작업 중 오류가 발생한 경우.
        """
        try:
            stmt = (
                update(self._model_class)
                .where(
                    (self._model_class.id == id)
                    & (self._model_class.is_deleted == False)
                )
                .values(is_deleted=True, deleted_at=datetime.utcnow())
                .returning(self._model_class)
            )
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise

    async def hard_delete(self, id: Any) -> Optional[ST]:
        """주어진 ID에 해당하는 모델 인스턴스를 데이터베이스에서 완전히 삭제합니다.

        Args:
            id (Any): 삭제할 모델 인스턴스의 ID입니다.

        Returns:
            Optional[ST]: 삭제된 모델 인스턴스 또는 None (인스턴스가 없는 경우)입니다.

        Raises:
            SQLAlchemyError: 데이터베이스 작업 중 오류가 발생한 경우.
        """
        return await super().delete(id)

    async def list_all(self) -> List[ST]:
        """삭제된 인스턴스를 포함한 모든 모델 인스턴스를 조회합니다.

        Returns:
            List[ST]: 모든 모델 인스턴스의 리스트입니다.
        """
        stmt = select(self._model_class)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def restore(self, id: Any) -> Optional[ST]:
        """소프트 삭제된 모델 인스턴스를 복원합니다.

        Args:
            id (Any): 복원할 모델 인스턴스의 ID입니다.

        Returns:
            Optional[ST]: 복원된 모델 인스턴스 또는 None (인스턴스가 없거나 이미 복원된 경우)입니다.

        Raises:
            SQLAlchemyError: 데이터베이스 작업 중 오류가 발생한 경우.
        """
        try:
            stmt = (
                update(self._model_class)
                .where(
                    (self._model_class.id == id)
                    & (self._model_class.is_deleted == True)
                )
                .values(is_deleted=False, deleted_at=None)
                .returning(self._model_class)
            )
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise
