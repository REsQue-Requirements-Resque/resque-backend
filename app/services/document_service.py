from app.repositories.document_repository import DocumentRepository
from app.services.base_service import BaseService
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse
from app.models.document import Document
from typing import Type


class DocumentService(BaseService):
    repository: Type[DocumentRepository] = DocumentRepository
    model = Document
    create_schema = DocumentCreate
    update_schema = DocumentUpdate
    response_schema = DocumentResponse

    def __init__(self, document_repository: DocumentRepository):
        self._repository = document_repository
        super().__init__(document_repository)
