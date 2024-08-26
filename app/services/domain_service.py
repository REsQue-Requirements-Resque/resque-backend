from app.services.base_service import BaseService
from app.schemas.domain import DomainCreate, DomainUpdate, DomainResponse
from app.repositories.domain_repository import DomainRepository
from app.models.domain import Domain
from typing import Type


class DomainService(BaseService):
    repository: Type[DomainRepository] = DomainRepository
    model = Domain
    create_schema = DomainCreate
    update_schema = DomainUpdate
    response_schema = DomainResponse

    def __init__(self, repository):
        super().__init__(repository)
