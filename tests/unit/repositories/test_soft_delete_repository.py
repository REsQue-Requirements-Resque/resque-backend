import pytest
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped
from sqlalchemy.sql.expression import delete
from datetime import datetime, timedelta
from app.models.base_model import BaseModel
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
from app.repositories.soft_delete_base_repository import SoftDeleteBaseRepository


class TestSoftDeleteModel(BaseModel, SoftDeleteMixin):
    name: Mapped[str] = Column(String)


class TestSoftDeleteRepository(SoftDeleteBaseRepository):
    _model_class = TestSoftDeleteModel


@pytest.mark.asyncio
class TestSoftDeleteBaseRepository:
    @pytest.fixture(autouse=True)
    async def setup(self, db_session):
        self.repo = TestSoftDeleteRepository(db_session)
        # 각 테스트 전에 테이블을 비웁니다
        await db_session.execute(delete(TestSoftDeleteModel))
        await db_session.commit()

    async def test_create(self):
        obj: TestSoftDeleteModel = await self.repo.create({"name": "Test Object"})
        assert obj.id is not None
        assert obj.name == "Test Object"
        assert obj.is_deleted == False
        assert obj.deleted_at is None

    async def test_get(self):
        obj = await self.repo.create({"name": "Test Object"})
        retrieved_obj = await self.repo.get(obj.id)
        assert retrieved_obj is not None
        assert retrieved_obj.id == obj.id
        assert retrieved_obj.name == "Test Object"

    async def test_list(self):
        await self.repo.create({"name": "Test Object 1"})
        await self.repo.create({"name": "Test Object 2"})
        await self.repo.create({"name": "Test Object 3"})
        await self.repo.delete(
            (await self.repo.list())[0].id
        )  # 첫 번째 객체 소프트 삭제
        objects = await self.repo.list()
        assert len(objects) == 2
        assert objects[0].name == "Test Object 2"
        assert objects[1].name == "Test Object 3"

    async def test_update(self):
        obj = await self.repo.create({"name": "Test Object"})
        updated_obj = await self.repo.update(obj.id, {"name": "Updated Test Object"})
        assert updated_obj.id == obj.id
        assert updated_obj.name == "Updated Test Object"

    async def test_soft_delete(self):
        obj = await self.repo.create({"name": "Test Object"})
        deleted_obj = await self.repo.delete(obj.id)
        assert deleted_obj is not None
        assert deleted_obj.id == obj.id
        assert deleted_obj.is_deleted == True
        assert deleted_obj.deleted_at is not None
        retrieved_obj = await self.repo.get(obj.id)
        assert retrieved_obj is None

    async def test_hard_delete(self):
        obj = await self.repo.create({"name": "Test Object"})
        deleted_obj = await self.repo.hard_delete(obj.id)
        assert deleted_obj is not None
        assert deleted_obj.id == obj.id
        retrieved_obj = await self.repo.get(obj.id)
        assert retrieved_obj is None
        all_objects = await self.repo.list_all()
        assert len(all_objects) == 0

    async def test_list_all(self):
        await self.repo.create({"name": "Test Object 1"})
        await self.repo.create({"name": "Test Object 2"})
        await self.repo.create({"name": "Test Object 3"})
        await self.repo.delete(
            (await self.repo.list())[0].id
        )  # 첫 번째 객체 소프트 삭제
        all_objects = await self.repo.list_all()
        assert len(all_objects) == 3
        assert sum(1 for obj in all_objects if obj.is_deleted) == 1

    async def test_restore(self):
        obj = await self.repo.create({"name": "Test Object"})
        await self.repo.delete(obj.id)
        restored_obj = await self.repo.restore(obj.id)
        assert restored_obj is not None
        assert restored_obj.id == obj.id
        assert restored_obj.is_deleted == False
        assert restored_obj.deleted_at is None
        retrieved_obj = await self.repo.get(obj.id)
        assert retrieved_obj is not None

    async def test_get_nonexistent(self):
        obj = await self.repo.get(999)  # 존재하지 않는 ID
        assert obj is None

    async def test_delete_nonexistent(self):
        obj = await self.repo.delete(999)  # 존재하지 않는 ID
        assert obj is None

    async def test_restore_nonexistent(self):
        obj = await self.repo.restore(999)  # 존재하지 않는 ID
        assert obj is None

    async def test_restore_non_deleted(self):
        obj = await self.repo.create({"name": "Test Object"})
        restored_obj = await self.repo.restore(obj.id)
        assert restored_obj is None
