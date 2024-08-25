"""
이 모듈은 Project 모델에 대한 데이터베이스 작업을 처리하는 저장소 클래스를 정의합니다.
BaseRepository를 상속받아 기본적인 CRUD 작업을 재사용하고, Project 모델에 특화된 추가 메서드를 제공합니다.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository):
    """
    Project 모델에 대한 데이터베이스 작업을 처리하는 저장소 클래스입니다.
    BaseRepository를 상속받아 기본적인 CRUD 작업을 재사용하고,
    Project 모델에 특화된 추가 메서드를 제공합니다.
    """

    _model_class = Project

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)

    async def get_by_title_and_founder(
        self, title: str, founder_id: int
    ) -> Optional[Project]:
        """
        제목과 창립자 ID로 프로젝트를 조회합니다.

        :param title: 프로젝트 제목
        :param founder_id: 창립자 ID
        :return: 조회된 Project 인스턴스 또는 None
        """
        stmt = (
            select(self._model_class)
            .where(
                self._model_class.title == title,
                self._model_class.founder_id == founder_id,
            )
            .options(selectinload(self._model_class.founder))
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_founder(self, founder_id: int) -> List[Project]:
        """
        특정 창립자의 모든 프로젝트를 조회합니다.

        :param founder_id: 창립자 ID
        :return: 해당 창립자의 모든 Project 인스턴스 리스트
        """
        stmt = (
            select(self._model_class)
            .where(self._model_class.founder_id == founder_id)
            .options(selectinload(self._model_class.founder))
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())
