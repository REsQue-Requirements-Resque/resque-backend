from sqlalchemy import Column, Integer, String, DateTime
from pydantic import BaseModel
from datetime import datetime
from app.models.base_model import BaseModel as SQLABaseModel
from app.services.base_service import BaseService
from app.repositories.soft_delete_base_repository import SoftDeleteBaseRepository
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
import pytest
from fastapi import HTTPException
from sqlalchemy import delete
from app.schemas.base_schema import (
    PaginatedResponse,
    ResponseSchema,
    CreateSchema,
    UpdateSchema,
)
from datetime import datetime, timedelta


class TestModel(SQLABaseModel, SoftDeleteMixin):
    __tablename__ = "test_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)


class TestCreateSchema(CreateSchema):
    name: str
    description: str


class TestUpdateSchema(UpdateSchema):
    name: str | None = None
    description: str | None = None


class TestResponseSchema(ResponseSchema):
    id: int
    name: str
    description: str
    is_deleted: bool
    deleted_at: datetime | None

    class Config:
        from_attributes = True


class TestPaginatedResponse(PaginatedResponse[TestResponseSchema]):
    pass


class TestRepository(SoftDeleteBaseRepository):
    _model_class = TestModel


class TestService(BaseService):
    repository = TestRepository
    model = TestModel
    create_schema = TestCreateSchema
    update_schema = TestUpdateSchema
    response_schema = TestResponseSchema


@pytest.mark.asyncio
class TestSoftDeleteBaseService:
    @pytest.fixture(autouse=True)
    async def setup(self, db_session):
        self.repository = TestRepository(db_session)
        self.service = TestService(self.repository)

        # 테이블 초기화
        await db_session.execute(delete(TestModel))
        await db_session.commit()

    async def test_create(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        result = await self.service.create(obj_in)
        assert isinstance(result, TestResponseSchema)
        assert result.name == "Test Object"
        assert result.description == "This is a test"
        assert result.is_deleted == False
        assert result.deleted_at is None

    async def test_get(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        result = await self.service.get(created.id)
        assert isinstance(result, TestResponseSchema)
        assert result.id == created.id
        assert result.name == created.name
        assert result.is_deleted == False

    async def test_list(self):
        obj_in1 = TestCreateSchema(name="Test Object 1", description="This is test 1")
        obj_in2 = TestCreateSchema(name="Test Object 2", description="This is test 2")
        await self.service.create(obj_in1)
        await self.service.create(obj_in2)
        result = await self.service.list()
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 2
        assert all(isinstance(item, TestResponseSchema) for item in result.items)
        assert all(not item.is_deleted for item in result.items)

    async def test_update(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        update_in = TestUpdateSchema(name="Updated Test Object")
        result = await self.service.update(created.id, update_in)
        assert isinstance(result, TestResponseSchema)
        assert result.id == created.id
        assert result.name == "Updated Test Object"
        assert result.description == "This is a test"
        assert result.is_deleted == False

    async def test_soft_delete(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        result = await self.service.delete(created.id)
        assert isinstance(result, TestResponseSchema)
        assert result.id == created.id
        assert result.is_deleted == True
        assert result.deleted_at is not None

        # Soft deleted item should not be retrieved by get
        with pytest.raises(HTTPException) as excinfo:
            await self.service.get(created.id)
        assert excinfo.value.status_code == 404

        # Soft deleted item should not be in the list
        list_result = await self.service.list()
        assert len(list_result.items) == 0

    async def test_list_all(self):
        obj_in1 = TestCreateSchema(name="Test Object 1", description="This is test 1")
        obj_in2 = TestCreateSchema(name="Test Object 2", description="This is test 2")
        created1 = await self.service.create(obj_in1)
        await self.service.create(obj_in2)
        await self.service.delete(created1.id)  # Soft delete the first item

        result = await self.repository.list_all()
        assert len(result) == 2
        assert any(item.is_deleted for item in result)
        assert any(not item.is_deleted for item in result)

    async def test_restore(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        await self.service.delete(created.id)  # Soft delete

        restored = await self.repository.restore(created.id)
        assert restored is not None
        assert restored.is_deleted == False
        assert restored.deleted_at is None

        # Restored item should be retrievable
        retrieved = await self.service.get(created.id)
        assert retrieved is not None
        assert retrieved.is_deleted == False

    async def test_hard_delete(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        await self.repository.hard_delete(created.id)

        # Item should not exist after hard delete
        with pytest.raises(HTTPException) as excinfo:
            await self.service.get(created.id)
        assert excinfo.value.status_code == 404

        # Item should not be in the list_all result
        all_items = await self.repository.list_all()
        assert len(all_items) == 0

    async def test_update_soft_deleted(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        await self.service.delete(created.id)  # Soft delete

        # Attempt to update soft-deleted item
        update_in = TestUpdateSchema(name="Updated Test Object")
        with pytest.raises(HTTPException) as excinfo:
            await self.service.update(created.id, update_in)
        assert excinfo.value.status_code == 404

    async def test_delete_already_deleted(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        await self.service.delete(created.id)  # Soft delete

        # Attempt to delete already soft-deleted item
        with pytest.raises(HTTPException) as excinfo:
            await self.service.delete(created.id)
        assert excinfo.value.status_code == 404

    async def test_list_with_pagination(self):
        for i in range(15):  # Create 15 objects
            obj_in = TestCreateSchema(
                name=f"Test Object {i}", description=f"This is test {i}"
            )
            await self.service.create(obj_in)

        # Test first page
        result = await self.service.list(skip=0, limit=10)
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 10
        assert result.total == 15
        assert result.page == 1
        assert result.size == 10

        # Test second page
        result = await self.service.list(skip=10, limit=10)
        assert len(result.items) == 5
        assert result.total == 15
        assert result.page == 2
        assert result.size == 10

    async def test_get_non_existent(self):
        with pytest.raises(HTTPException) as excinfo:
            await self.service.get(999)  # Assuming 999 doesn't exist
        assert excinfo.value.status_code == 404

    async def test_update_non_existent(self):
        update_in = TestUpdateSchema(name="Updated Test Object")
        with pytest.raises(HTTPException) as excinfo:
            await self.service.update(999, update_in)  # Assuming 999 doesn't exist
        assert excinfo.value.status_code == 404

    async def test_delete_non_existent(self):
        with pytest.raises(HTTPException) as excinfo:
            await self.service.delete(999)  # Assuming 999 doesn't exist
        assert excinfo.value.status_code == 404
