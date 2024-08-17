from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, Project)

    async def get(self, project_id: int) -> Optional[Project]:
        stmt = (
            select(self.model)
            .where(self.model.id == project_id)
            .options(selectinload(self.model.founder))
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> List[Project]:
        stmt = select(self.model).options(selectinload(self.model.founder))
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_title_and_founder(
        self, title: str, founder_id: int
    ) -> Optional[Project]:
        stmt = (
            select(self.model)
            .where(self.model.title == title, self.model.founder_id == founder_id)
            .options(selectinload(self.model.founder))
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_founder(self, founder_id: int) -> List[Project]:
        stmt = (
            select(self.model)
            .where(self.model.founder_id == founder_id)
            .options(selectinload(self.model.founder))
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())
