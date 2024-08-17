from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.base_service import BaseService


class ProjectService(BaseService[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self, project_repo: ProjectRepository):
        super().__init__(project_repo)
        self.project_repo = project_repo

    async def create_project(
        self, project_data: ProjectCreate, current_user_id: int
    ) -> Project:
        try:
            existing_project = await self.project_repo.get_by_title_and_founder(
                project_data.title, current_user_id
            )
            if existing_project:
                raise HTTPException(
                    status_code=400,
                    detail="A project with this title already exists for this user",
                )

            project_dict = project_data.model_dump()
            project_dict["founder_id"] = current_user_id
            return await super().create(ProjectCreate(**project_dict))
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update_project(
        self, project_id: int, project_data: ProjectUpdate, current_user_id: int
    ) -> Project:
        existing_project = await self.get(project_id)
        if existing_project.founder_id != current_user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to update this project"
            )
        return await super().update(project_id, project_data)

    async def delete_project(self, project_id: int, current_user_id: int) -> bool:
        project = await self.get(project_id)
        if project.founder_id != current_user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this project"
            )
        return await super().delete(project_id)

    async def list_projects_by_founder(self, founder_id: int) -> List[Project]:
        try:
            return await self.project_repo.list_by_founder(founder_id)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_project_by_title_and_founder(
        self, title: str, founder_id: int
    ) -> Optional[Project]:
        return await self.project_repo.get_by_title_and_founder(title, founder_id)
