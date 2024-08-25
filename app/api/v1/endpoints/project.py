from app.api.base_crud_endpoint import BaseCrudEndpoint
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.core.permissions import IsAuthenticated
from app.api.endpoint_action import EndpointAction
from app.schemas.document import DocumentResponse
from typing import List
from app.dependencies.get_service import get_service


class ProjectEndpoint(BaseCrudEndpoint):
    prefix = "/projects"
    tags = ["projects"]
    _service_cls = ProjectService
    create_schema = ProjectCreate
    update_schema = ProjectUpdate
    response_schema = ProjectResponse

    def __init__(self, router):
        super().__init__(router)

    def register_custom_actions(self):
        document_action = EndpointAction(
            func=self.documents,
            additional_path="/documents",
            methods=["GET"],
            is_detail=True,
            response_model=List[DocumentResponse],
            permissions=[IsAuthenticated],
            summary="List all documents of a project",
        )
        document_action.register(self.router, prefix=self.prefix)

    async def documents(self, id: int):
        project_service = get_service(ProjectService)
        return await project_service.get_documents_by_project_id(id)
