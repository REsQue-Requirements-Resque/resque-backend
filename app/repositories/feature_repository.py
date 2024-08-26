from app.repositories.base_repository import BaseRepository
from app.models.feature import Feature
from sqlalchemy.ext.asyncio import AsyncSession


class FeatureRepository(BaseRepository):
    _model_class = Feature

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
