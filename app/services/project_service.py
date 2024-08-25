from typing import List, Optional, Type
from fastapi import HTTPException, Depends
from sqlalchemy.exc import SQLAlchemyError
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.services.base_service import BaseService
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse


class ProjectService(BaseService):
    repository: Type[ProjectRepository] = ProjectRepository
    model = Project
    create_schema = ProjectCreate
    update_schema = ProjectUpdate
    response_schema = ProjectResponse

    def __init__(self, repository: ProjectRepository):
        super().__init__(repository)

    async def create_project(self, project_data: ProjectCreate) -> ProjectResponse:
        try:
            current_user_id = self.context.user_id
            existing_project = await self.get_project_by_title_and_founder(
                project_data.title, current_user_id
            )
            if existing_project:
                raise HTTPException(
                    status_code=400,
                    detail="A project with this title already exists for this user",
                )

            project_dict = project_data.model_dump()
            project_dict["founder_id"] = current_user_id
            return await self.create(ProjectCreate(**project_dict))
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def list_projects_by_founder(self) -> List[ProjectResponse]:
        try:
            founder_id = self.context.user_id
            projects = await self.repository.list_by_founder(founder_id)
            return [ProjectResponse.model_validate(project) for project in projects]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_project_by_title_and_founder(
        self, title: str
    ) -> Optional[ProjectResponse]:
        try:
            founder_id = self.context.user_id
            project = await self.repository.get_by_title_and_founder(title, founder_id)
            return ProjectResponse.model_validate(project) if project else None
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def check_project_owner(self, project_id: int) -> None:
        project = await self.get(project_id)
        if project.founder_id != self.context.user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this project"
            )

    async def update_project(
        self, project_id: int, project_data: ProjectUpdate
    ) -> ProjectResponse:
        await self.check_project_owner(project_id)
        return await self.update(project_id, project_data)

    async def delete_project(self, project_id: int) -> ProjectResponse:
        await self.check_project_owner(project_id)
        return await self.delete(project_id)
