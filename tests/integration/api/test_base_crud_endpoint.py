import pytest
from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute
from httpx import AsyncClient
from app.api.base_crud_endpoint import BaseCrudEndpoint
from app.schemas.base_schema import (
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
    PaginatedResponse,
)
from app.services.base_service import BaseService
from app.repositories.base_repository import BaseRepository
from app.models.base_model import BaseModel
from app.api.endpoint_action import EndpointAction
from app.core.permissions import IsAllowAny
from app.dependencies.get_service import get_service
from sqlalchemy.orm import Mapped, mapped_column


class TestModel(BaseModel):

    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)


class TestCreateSchema(CreateSchema):
    title: str
    description: str


class TestUpdateSchema(UpdateSchema):
    title: str | None
    description: str | None


class TestResponseSchema(ResponseSchema):
    title: str
    description: str


class TestRepository(BaseRepository):
    model = TestModel


class TestService(BaseService):
    repository = TestRepository


class TestCrudEndpoint(BaseCrudEndpoint):
    prefix = "/test"
    _service_cls = TestService
    create_schema = TestCreateSchema
    update_schema = TestUpdateSchema
    response_schema = TestResponseSchema

    def register_custom_actions(self):
        custom_action = EndpointAction(
            func=self.custom_action,
            methods=["POST"],
            is_detail=False,
            additional_path="/custom",
            response_model=self.response_schema,
            permissions=[IsAllowAny],
            summary="Custom action",
        )
        custom_action.register(self.router, self.prefix)

    async def custom_action(self, *args, **kwargs):
        return {"message": "Custom action success"}


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
class TestBaseCrudEndpoint:
    @pytest.fixture
    def router(self):
        router = APIRouter()
        return router

    @pytest.fixture
    def test_crud_endpoint(self, router):
        return TestCrudEndpoint(router)

    @pytest.fixture
    def test_service(self):
        return get_service(TestService)

    @pytest.fixture
    def app(self, router):
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    async def client(self, app):
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            yield client

    async def test_create_item(self, client, test_service):
        item_data = {"title": "Test Item", "description": "This is a test item"}
        response = await client.post("/test", json=item_data)
        assert response.status_code == 201
        created_item = response.json()
        assert created_item["title"] == item_data["title"]
        assert created_item["description"] == item_data["description"]

    async def test_get_item(self, client, test_service):
        # 먼저 아이템을 생성합니다
        item_data = {"title": "Test Item", "description": "This is a test item"}
        create_response = await client.post("/test", json=item_data)
        created_item = create_response.json()

        # 생성된 아이템을 조회합니다
        response = await client.get(f"/test/{created_item['id']}")
        assert response.status_code == 200
        retrieved_item = response.json()
        assert retrieved_item["title"] == item_data["title"]
        assert retrieved_item["description"] == item_data["description"]

    async def test_update_item(self, client, test_service):
        # 먼저 아이템을 생성합니다
        item_data = {"title": "Test Item", "description": "This is a test item"}
        create_response = await client.post("/test", json=item_data)
        created_item = create_response.json()

        # 아이템을 업데이트합니다
        update_data = {
            "title": "Updated Item",
            "description": "This is an updated item",
        }
        response = await client.put(f"/test/{created_item['id']}", json=update_data)
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["title"] == update_data["title"]
        assert updated_item["description"] == update_data["description"]

    async def test_delete_item(self, client, test_service):
        # 먼저 아이템을 생성합니다
        item_data = {"title": "Test Item", "description": "This is a test item"}
        create_response = await client.post("/test", json=item_data)
        created_item = create_response.json()

        # 아이템을 삭제합니다
        response = await client.delete(f"/test/{created_item['id']}")
        assert response.status_code == 204

        # 삭제된 아이템을 조회하여 404 응답을 확인합니다
        get_response = await client.get(f"/test/{created_item['id']}")
        assert get_response.status_code == 404

    async def test_list_items(self, client, test_service):
        # 여러 아이템을 생성합니다
        for i in range(5):
            item_data = {
                "title": f"Test Item {i}",
                "description": f"This is test item {i}",
            }
            await client.post("/test", json=item_data)

        # 아이템 목록을 조회합니다
        response = await client.get("/test")
        assert response.status_code == 200
        items = response.json()
        assert len(items["items"]) == 5
        assert items["total"] == 5

    async def test_custom_action(self, client, test_service):
        response = await client.post("/test/custom")
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == "Custom action success"
