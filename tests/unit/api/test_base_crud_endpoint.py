import pytest
from fastapi import APIRouter
from app.api.base_crud_endpoint import BaseCrudEndpoint
from app.schemas.base_schema import (
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
    PaginatedResponse,
)
from app.services.base_service import BaseService
from app.exceptions.exceptions import PageNotFound


# 목업 클래스 정의
class MockService(BaseService):
    async def create(self, data, user):
        return {"id": 1, **data.dict()}

    async def list(self, user, page, page_size):
        return [{"id": 1, "name": "Test"}], 1

    async def get(self, id):
        if id == 1:
            return {"id": 1, "name": "Test"}
        return None

    async def update(self, id, data, user):
        if id == 1:
            return {"id": 1, **data.dict()}
        return None

    async def delete(self, id, user):
        return id == 1


class MockCreateSchema(CreateSchema):
    name: str


class MockUpdateSchema(UpdateSchema):
    name: str


class MockResponseSchema(ResponseSchema):
    id: int
    name: str


class MockCrudEndpoint(BaseCrudEndpoint):
    prefix = "/test"
    _service_cls = MockService
    create_schema = MockCreateSchema
    update_schema = MockUpdateSchema
    response_schema = MockResponseSchema


@pytest.mark.asyncio
class TestBaseCrudEndpoint:
    @pytest.fixture
    async def endpoint(self):
        router = APIRouter()
        return MockCrudEndpoint(router)

    async def test_create(self, endpoint):
        data = MockCreateSchema(name="Test Item")
        result = await endpoint.create(data, current_user={"id": 1})
        assert result == {"id": 1, "name": "Test Item"}

    async def test_list(self, endpoint):
        result = await endpoint.list(current_user={"id": 1})
        assert isinstance(result, PaginatedResponse)
        assert result.total == 1
        assert result.items == [{"id": 1, "name": "Test"}]

    async def test_retrieve_success(self, endpoint):
        result = await endpoint.retrieve(1, current_user={"id": 1})
        assert result == {"id": 1, "name": "Test"}

    async def test_retrieve_not_found(self, endpoint):
        with pytest.raises(PageNotFound):
            await endpoint.retrieve(2, current_user={"id": 1})

    async def test_update_success(self, endpoint):
        data = MockUpdateSchema(name="Updated Item")
        result = await endpoint.update(1, data, current_user={"id": 1})
        assert result == {"id": 1, "name": "Updated Item"}

    async def test_update_not_found(self, endpoint):
        data = MockUpdateSchema(name="Updated Item")
        with pytest.raises(PageNotFound):
            await endpoint.update(2, data, current_user={"id": 1})

    async def test_delete_success(self, endpoint):
        result = await endpoint.delete(1, current_user={"id": 1})
        assert result is None

    async def test_delete_not_found(self, endpoint):
        with pytest.raises(PageNotFound):
            await endpoint.delete(2, current_user={"id": 1})

    def test_register_default_routes(self, endpoint):
        assert len(endpoint.router.routes) == 5  # 기본 CRUD 작업에 대한 5개의 라우트

    # 추가 테스트: custom actions, 권한 검사 등
