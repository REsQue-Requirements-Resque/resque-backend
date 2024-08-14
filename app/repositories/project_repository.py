from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.models.project import Project
from typing import List, Optional, Dict, Any, Union


class ProjectRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, project: Project) -> Project:
        self.db_session.add(project)
        await self.db_session.commit()
        await self.db_session.refresh(project)
        return project

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
        return result.scalars().all()

    async def update(
        self, project_id: int, project_data: Dict[str, Any]
    ) -> Optional[Project]:
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(**project_data)
            .returning(Project)
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.scalar_one_or_none()

    async def delete(self, project_id: int) -> bool:
        stmt = delete(Project).where(Project.id == project_id)
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount > 0

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
        return result.scalars().all()
