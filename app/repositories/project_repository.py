from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, project_data: Dict[str, Any]) -> Project:
        try:
            db_project = Project(**project_data)
            self.db_session.add(db_project)
            await self.db_session.commit()
            await self.db_session.refresh(db_project)
            return db_project
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise e

    async def get(self, project_id: int) -> Optional[Project]:
        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.founder))
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> List[Project]:
        stmt = select(Project).options(selectinload(Project.founder))
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, project_id: int, update_data: Dict[str, Any]
    ) -> Optional[Project]:
        try:
            stmt = (
                update(Project)
                .where(Project.id == project_id)
                .values(**update_data)
                .returning(Project)
            )
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise e

    async def delete(self, project_id: int) -> bool:
        try:
            stmt = delete(Project).where(Project.id == project_id)
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise e

    async def get_by_title_and_founder(
        self, title: str, founder_id: int
    ) -> Optional[Project]:
        stmt = (
            select(Project)
            .where(Project.title == title, Project.founder_id == founder_id)
            .options(selectinload(Project.founder))
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_founder(self, founder_id: int) -> List[Project]:
        stmt = (
            select(Project)
            .where(Project.founder_id == founder_id)
            .options(selectinload(Project.founder))
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())
