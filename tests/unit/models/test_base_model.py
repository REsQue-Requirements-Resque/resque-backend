import pytest
from sqlalchemy import Column, String
from app.models.base_model import BaseModel
import pydantic


class TestModel(BaseModel):
    name = Column(String)


class TestSchema(pydantic.BaseModel):
    name: str


@pytest.mark.unit
@pytest.mark.models
class TestBaseModel:
    @pytest.mark.asyncio
    async def test_id_column(self):
        model = TestModel()
        assert hasattr(model, "id")
        assert isinstance(model.id, int) or model.id is None

    def test_tablename(self):
        assert TestModel.__tablename__ == "testmodels"

    def test_repr(self):
        model = TestModel(id=1, name="Test")
        assert repr(model) == "<TestModel(id=1)>"

    @pytest.mark.asyncio
    async def test_from_schema(self):
        schema = TestSchema(name="Test")
        model = TestModel.from_schema(schema)
        assert isinstance(model, TestModel)
        assert model.name == "Test"

    @pytest.mark.asyncio
    @pytest.mark.using_db
    async def test_create_and_query(self, db_session):
        schema = TestSchema(name="Test")
        model = TestModel.from_schema(schema)
        db_session.add(model)
        await db_session.commit()

        queried_model = await db_session.get(TestModel, model.id)
        assert queried_model is not None
        assert queried_model.name == "Test"
