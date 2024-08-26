from app.api.base_crud_endpoint import BaseCrudEndpoint
from app.services.domain_service import DomainService
from app.schemas.domain import (
    DomainCreate,
    DomainUpdate,
    DomainResponse,
)


class DomainEndpoint(BaseCrudEndpoint):
    prefix = "/domains"
    tags = ["domains"]
    _service_cls = DomainService
    create_schema = DomainCreate
    update_schema = DomainUpdate
    response_schema = DomainResponse

    def __init__(self, router):
        super().__init__(router)
