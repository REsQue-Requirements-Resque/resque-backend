import pytest
from sqlalchemy.sql.expression import delete
from app.models.base_model import BaseModel
from app.repositories.base_repository import BaseRepository
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped


class TestModel(BaseModel):
    __tablename__ = "test_models"

    name: Mapped[str] = Column(String)


class TestRepository(BaseRepository):
    _model_class = TestModel


@pytest.mark.asyncio
class TestBaseRepository:
    @pytest.fixture(autouse=True)
    async def setup(self, db_session):
        self.repo = TestRepository(db_session)
        # 각 테스트 전에 테이블을 비웁니다
        await db_session.execute(delete(TestModel))
        await db_session.flush()

    async def test_create(self):
        obj: TestModel = await self.repo.create({"name": "Test Object"})
        assert obj.id is not None
        assert obj.name == "Test Object"

    async def test_get(self):
        obj = await self.repo.create({"name": "Test Object"})
        retrieved_obj = await self.repo.get(obj.id)
        assert retrieved_obj is not None
        assert retrieved_obj.id == obj.id
        assert retrieved_obj.name == "Test Object"

    async def test_list(self):
        await self.repo.create({"name": "Test Object 1"})
        await self.repo.create({"name": "Test Object 2"})
        objects = await self.repo.list()
        assert len(objects) == 2
        assert objects[0].name == "Test Object 1"
        assert objects[1].name == "Test Object 2"

    async def test_update(self):
        obj = await self.repo.create({"name": "Test Object"})
        updated_obj = await self.repo.update(obj, {"name": "Updated Test Object"})
        assert updated_obj.id == obj.id
        assert updated_obj.name == "Updated Test Object"

    async def test_delete(self):
        obj = await self.repo.create({"name": "Test Object"})
        deleted_obj = await self.repo.delete(obj.id)
        assert deleted_obj is not None
        assert deleted_obj.id == obj.id
        retrieved_obj = await self.repo.get(obj.id)
        assert retrieved_obj is None

    async def test_get_nonexistent(self):
        obj = await self.repo.get(999)  # 존재하지 않는 ID
        assert obj is None

    async def test_delete_nonexistent(self):
        obj = await self.repo.delete(999)  # 존재하지 않는 ID
        assert obj is None
