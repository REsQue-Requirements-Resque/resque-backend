import pytest
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import Column, Integer, String, DateTime
from pydantic import BaseModel
from app.models.base_model import BaseModel as SQLABaseModel
from app.repositories.base_repository import BaseRepository
from app.services.base_service import BaseService
from app.schemas.base_schema import PaginatedResponse
from sqlalchemy.sql.expression import delete


# TestModel 정의
class TestModel(SQLABaseModel):
    __tablename__ = "test_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)


# TestCreateSchema 정의
class TestCreateSchema(BaseModel):
    name: str
    description: str


# TestUpdateSchema 정의
class TestUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None


# TestResponseSchema 정의
class TestResponseSchema(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


# TestRepository 정의
class TestRepository(BaseRepository):
    _model_class = TestModel


# TestService 정의
class TestService(BaseService):
    repository = TestRepository
    model = TestModel
    create_schema = TestCreateSchema
    update_schema = TestUpdateSchema
    response_schema = TestResponseSchema


@pytest.mark.asyncio
class TestBaseService:
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

    async def test_get(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        result = await self.service.get(created.id)
        assert isinstance(result, TestResponseSchema)
        assert result.id == created.id
        assert result.name == created.name

    async def test_list(self):
        obj_in1 = TestCreateSchema(name="Test Object 1", description="This is test 1")
        obj_in2 = TestCreateSchema(name="Test Object 2", description="This is test 2")
        await self.service.create(obj_in1)
        await self.service.create(obj_in2)
        result = await self.service.list()
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 2
        assert all(isinstance(item, TestResponseSchema) for item in result.items)

    async def test_update(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        update_in = TestUpdateSchema(name="Updated Test Object")
        result = await self.service.update(created.id, update_in)
        assert isinstance(result, TestResponseSchema)
        assert result.id == created.id
        assert result.name == "Updated Test Object"
        assert result.description == "This is a test"

    async def test_delete(self):
        obj_in = TestCreateSchema(name="Test Object", description="This is a test")
        created = await self.service.create(obj_in)
        result = await self.service.delete(created.id)
        assert isinstance(result, TestResponseSchema)
        assert result.id == created.id
        with pytest.raises(HTTPException) as excinfo:
            await self.service.get(created.id)
        assert excinfo.value.status_code == 404
