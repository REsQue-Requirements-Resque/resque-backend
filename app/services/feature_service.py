from app.services.base_service import BaseService
from app.schemas.feature import FeatureCreate, FeatureUpdate, FeatureResponse
from app.repositories.feature_repository import FeatureRepository
from app.models.feature import Feature
from typing import Type


class FeatureService(BaseService):
    repository: Type[FeatureRepository] = FeatureRepository
    model = Feature
    create_schema = FeatureCreate
    update_schema = FeatureUpdate
    response_schema = FeatureResponse

    def __init__(self, repository):
        super().__init__(repository)
