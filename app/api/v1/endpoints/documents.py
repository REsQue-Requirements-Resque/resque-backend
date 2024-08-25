from fastapi import APIRouter, status
from app.api.base_crud_endpoint import BaseCrudEndpoint
from app.services.document_service import DocumentService
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse


class DocumentEndpoint(BaseCrudEndpoint):
    prefix = "/documents"
    tags = ["documents"]
    _service_cls = DocumentService
    create_schema = DocumentCreate
    update_schema = DocumentUpdate
    response_schema = DocumentResponse

    def __init__(self, router):
        super().__init__(router)
