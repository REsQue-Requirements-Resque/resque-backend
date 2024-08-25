from app.repositories.base_repository import BaseRepository
from app.models.requirement import Requirement
from sqlalchemy.ext.asyncio import AsyncSession


class RequirementRepository(BaseRepository):
    _model_class = Requirement

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
