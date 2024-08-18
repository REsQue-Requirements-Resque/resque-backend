import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_async_db
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectSchema
from app.services.project_service import ProjectService
from app.api.base_crud_endpoint import BaseCrudEndpoint

router = APIRouter()
logger = logging.getLogger(__name__)


class ProjectEndpoint(BaseCrudEndpoint[Project, ProjectSchema, ProjectService]):
    def __init__(self, router: APIRouter):
        super().__init__(router, "/projects")
        self.service_class = ProjectService
        self.schema = ProjectSchema


project_endpoint = ProjectEndpoint(router)
