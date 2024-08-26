from app.api.base_crud_endpoint import BaseCrudEndpoint
from app.services.feature_service import FeatureService
from app.schemas.feature import (
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
)


class FeatureEndpoint(BaseCrudEndpoint):
    prefix = "/features"
    tags = ["features"]
    _service_cls = FeatureService
    create_schema = FeatureCreate
    update_schema = FeatureUpdate
    response_schema = FeatureResponse

    def __init__(self, router):
        super().__init__(router)
