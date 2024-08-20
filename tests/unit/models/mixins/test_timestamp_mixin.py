import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped
from app.db.base import Base
from app.models.mixins.timestamp_mixin import TimestampMixin
from sqlalchemy.future import select
from freezegun import freeze_time
from datetime import datetime, timedelta, timezone


class TestModel(Base, TimestampMixin):
    __tablename__ = "test_timestamp_models"
    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.models
@pytest.mark.mixins
class TestTimestampMixin:
    async def test_timestamp_columns_exist(self):
        """created_at과 updated_at 컬럼의 존재를 검증합니다."""
        assert hasattr(
            TestModel, "created_at"
        ), "모델에 created_at 컬럼이 있어야 합니다"
        assert hasattr(
            TestModel, "updated_at"
        ), "모델에 updated_at 컬럼이 있어야 합니다"

    async def test_timestamp_column_properties(self):
        """created_at과 updated_at 컬럼의 속성을 검증합니다."""
        for column_name in ["created_at", "updated_at"]:
            column = getattr(TestModel, column_name).property.columns[0]
            assert (
                column.name == column_name
            ), f"컬럼 이름은 '{column_name}'이어야 합니다"
            assert (
                str(column.type) == "DATETIME"
            ), f"{column_name}은 DateTime 타입이어야 합니다"
            assert (
                column.nullable is False
            ), f"{column_name}은 nullable이 아니어야 합니다"
            assert (
                column.type.timezone is True
            ), f"{column_name}은 timezone이 True여야 합니다"

    @freeze_time("2023-01-01 00:00:00")
    async def test_create_with_timestamp(self, db_session):
        """모델 생성 시 timestamp 설정을 검증합니다."""
        model = TestModel(name="Test Model")
        db_session.add(model)
        await db_session.flush()

        queried_model = await db_session.get(TestModel, model.id)
        assert queried_model is not None
        assert queried_model.created_at == datetime.now(timezone.utc)
        assert queried_model.updated_at == datetime.now(timezone.utc)

    @freeze_time("2023-01-01 00:00:00")
    async def test_update_timestamp(self, db_session):
        """모델 업데이트 시 updated_at 변경을 검증합니다."""
        model = TestModel(name="Test Model")
        db_session.add(model)
        await db_session.flush()

        initial_time = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert model.created_at == initial_time
        assert model.updated_at == initial_time

        with freeze_time("2023-01-01 01:00:00"):
            model.name = "Updated Model"
            await db_session.flush()

            updated_model = await db_session.get(TestModel, model.id)
            assert updated_model.created_at == initial_time
            assert updated_model.updated_at == datetime(
                2023, 1, 1, 1, 0, 0, tzinfo=timezone.utc
            )

    @freeze_time("2023-01-01 00:00:00")
    async def test_bulk_insert_timestamp(self, db_session):
        """대량 삽입 시 timestamp 설정을 검증합니다."""
        models = [TestModel(name=f"Model {i}") for i in range(5)]
        db_session.add_all(models)
        await db_session.flush()

        stmt = select(TestModel)
        result = await db_session.execute(stmt)
        queried_models = result.scalars().all()

        expected_time = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        for model in queried_models:
            assert model.created_at == expected_time
            assert model.updated_at == expected_time

    @freeze_time("2023-01-01 00:00:00")
    async def test_different_created_and_updated_at(self, db_session):
        """created_at과 updated_at이 다른 경우를 검증합니다."""
        model = TestModel(name="Test Model")
        db_session.add(model)
        await db_session.flush()

        with freeze_time("2023-01-01 01:00:00"):
            model.name = "Updated Model"
            await db_session.flush()

        updated_model = await db_session.get(TestModel, model.id)
        assert updated_model.updated_at > updated_model.created_at
        assert updated_model.updated_at - updated_model.created_at == timedelta(hours=1)

    async def test_multiple_models_with_timestamp(self):
        """여러 모델에서 TimestampMixin을 사용할 수 있는지 검증합니다."""

        class AnotherModel(Base, TimestampMixin):
            __tablename__ = "another_timestamp_models"
            id: Mapped[int] = Column(Integer, primary_key=True)

        for model in [TestModel, AnotherModel]:
            assert hasattr(model, "created_at")
            assert hasattr(model, "updated_at")
            assert model.created_at.property.columns[0].name == "created_at"
            assert model.updated_at.property.columns[0].name == "updated_at"
