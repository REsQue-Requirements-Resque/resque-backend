from fastapi import APIRouter

from app.api.v1.endpoints.root import router as root_router
from app.api.v1.endpoints.user import user_router
from app.api.v1.endpoints.project import ProjectEndpoint
from app.api.v1.endpoints.document import DocumentEndpoint
from app.api.v1.endpoints.domain import DomainEndpoint
from app.api.v1.endpoints.feature import FeatureEndpoint
from app.api.v1.endpoints.requirement import RequirementEndpoint

api_v1_router = APIRouter()

api_v1_router.include_router(root_router, tags=["root"], prefix="")
api = api_v1_router.include_router(user_router, tags=["users"], prefix="/users")
project_endpoint = ProjectEndpoint(api_v1_router)
document_endpoint = DocumentEndpoint(api_v1_router)
domain_endpoint = DomainEndpoint(api_v1_router)
feature_endpoint = FeatureEndpoint(api_v1_router)
requirement_endpoint = RequirementEndpoint(api_v1_router)
