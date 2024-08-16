from app.repositories.project_repository import ProjectRepository
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


class ProjectService:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def create_project(
        self, project_data: ProjectCreate, current_user_id: int
    ) -> Project:
        try:
            # 중복 프로젝트 확인
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
            return await self.project_repo.create(project_dict)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_project(self, project_id: int) -> Project:
        project = await self.project_repo.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    async def update_project(
        self, project_id: int, project_data: ProjectUpdate, current_user_id: int
    ) -> Project:
        try:
            existing_project = await self.get_project(project_id)
        except HTTPException as e:
            raise e

        if existing_project.founder_id != current_user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to update this project"
            )

        update_dict = project_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="No update data provided")

        updated_project = await self.project_repo.update(project_id, update_dict)
        if not updated_project:
            raise HTTPException(status_code=500, detail="Failed to update project")
        return updated_project

    async def delete_project(self, project_id: int, current_user_id: int) -> None:
        project = await self.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.founder_id != current_user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this project"
            )

        deleted = await self.project_repo.delete(project_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete project")

        return True

    async def list_projects(self) -> List[Project]:
        try:
            return await self.project_repo.list()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def list_projects_by_founder(self, founder_id: int) -> List[Project]:
        try:
            return await self.project_repo.list_by_founder(founder_id)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_project_by_title_and_founder(
        self, title: str, founder_id: int
    ) -> Optional[Project]:
        return await self.project_repo.get_by_title_and_founder(title, founder_id)
