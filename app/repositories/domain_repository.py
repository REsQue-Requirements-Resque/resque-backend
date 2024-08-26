from app.repositories.base_repository import BaseRepository
from app.models.domain import Domain
from sqlalchemy.ext.asyncio import AsyncSession


class DomainRepository(BaseRepository):
    _model_class = Domain

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
