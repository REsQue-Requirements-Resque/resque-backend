from app.api.base_crud_endpoint import BaseCrudEndpoint
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.core.permissions import IsAuthenticated
from app.api.endpoint_action import EndpointAction


class ProjectEndpoint(BaseCrudEndpoint):
    prefix = "/projects"
    tags = ["projects"]
    _service_cls = ProjectService
    create_schema = ProjectCreate
    update_schema = ProjectUpdate
    response_schema = ProjectResponse

    def __init__(self, router):
        super().__init__(router)
