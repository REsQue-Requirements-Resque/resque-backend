from typing import Any, List, Optional, Type
from app.models.document import Document
from app.repositories.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class DocumentRepository(BaseRepository):
    _model_class = Document

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
