import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_async_db
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService
from app.repositories.project_repository import ProjectRepository
from app.core.security import get_current_user
from app.models.user import User
from typing import List
from pydantic import ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_project_service(
    db: AsyncSession = Depends(get_async_db),
) -> ProjectService:
    project_repo = ProjectRepository(db)
    return ProjectService(project_repo)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: dict,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    logger.info(f"Received project data: {project_data}")
    try:
        project = ProjectCreate(**project_data)
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    try:
        created_project = await project_service.create_project(project, current_user.id)
        logger.info(f"Created project: {created_project}")
        return created_project
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the project",
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    project_service: ProjectService = Depends(get_project_service),
):
    return await project_service.get_project(project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    try:
        updated_project = await project_service.update_project(
            project_id, project_update, current_user.id
        )
        return updated_project
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    try:
        await project_service.delete_project(project_id, current_user.id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    project_service: ProjectService = Depends(get_project_service),
):
    return await project_service.list_projects()
