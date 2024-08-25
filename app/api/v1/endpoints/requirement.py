from app.api.base_crud_endpoint import BaseCrudEndpoint
from app.services.requirement_service import RequirementService
from app.schemas.requirement import (
    RequirementCreate,
    RequirementUpdate,
    RequirementResponse,
)


class RequirementEndpoint(BaseCrudEndpoint):
    prefix = "/requirements"
    tags = ["requirements"]
    _service_cls = RequirementService
    create_schema = RequirementCreate
    update_schema = RequirementUpdate
    response_schema = RequirementResponse

    def __init__(self, router):
        super().__init__(router)
