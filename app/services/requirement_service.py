from typing import List, Type
from app.services.base_service import BaseService
from app.schemas.requirement import (
    RequirementCreate,
    RequirementUpdate,
    RequirementResponse,
)
from app.models.requirement import Requirement
from app.repositories.requirement_repository import RequirementRepository


class RequirementService(BaseService):
    repository = RequirementRepository
    model = Requirement
    create_schema = RequirementCreate
    update_schema = RequirementUpdate
    response_schema = RequirementResponse

    def __init__(self, repository: RequirementRepository):
        super().__init__(repository)
