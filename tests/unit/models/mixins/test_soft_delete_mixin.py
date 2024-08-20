import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped
from app.db.base import Base
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
from sqlalchemy.future import select


class TestModel(Base, SoftDeleteMixin):
    __tablename__ = "test_soft_delete_models"
    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.models
@pytest.mark.mixins
class TestSoftDeleteMixin:
    async def test_is_deleted_column_exists(self):
        """is_deleted 컬럼의 존재를 검증합니다.

        Arrange:
            TestModel은 SoftDeleteMixin을 통해 is_deleted 컬럼이 정의되어 있습니다.
        Act:
            TestModel의 is_deleted 컬럼 속성을 검사합니다.
        Assert:
            is_deleted 컬럼이 존재해야 합니다.
        """
        assert hasattr(
            TestModel, "is_deleted"
        ), "모델에 is_deleted 컬럼이 있어야 합니다"

    async def test_is_deleted_column_properties(self):
        """is_deleted 컬럼의 속성을 검증합니다.

        Arrange:
            TestModel은 SoftDeleteMixin을 통해 is_deleted 컬럼이 정의되어 있습니다.
        Act:
            TestModel의 is_deleted 컬럼 속성을 검사합니다.
        Assert:
            is_deleted 컬럼은 Boolean 타입이고, nullable이 아니며, 기본값이 False여야 합니다.
        """
        is_deleted_column = TestModel.is_deleted.property.columns[0]
        assert (
            is_deleted_column.name == "is_deleted"
        ), "컬럼 이름은 'is_deleted'여야 합니다"
        assert (
            str(is_deleted_column.type) == "BOOLEAN"
        ), "is_deleted는 Boolean 타입이어야 합니다"
        assert (
            is_deleted_column.nullable is False
        ), "is_deleted는 nullable이 아니어야 합니다"
        assert (
            is_deleted_column.default.arg is False
        ), "is_deleted의 기본값은 False여야 합니다"

    async def test_create_and_query(self, db_session):
        """모델 생성 및 쿼리 기능을 검증합니다.

        Arrange:
            TestModel 인스턴스를 생성하고 데이터베이스에 저장합니다.
        Act:
            생성된 모델을 쿼리하고 is_deleted 값을 확인합니다.
        Assert:
            생성된 모델의 is_deleted 값이 False여야 합니다.
        """
        model = TestModel(name="Test Model")
        db_session.add(model)
        await db_session.flush()

        queried_model = await db_session.get(TestModel, model.id)
        assert queried_model is not None
        assert queried_model.is_deleted is False

    async def test_soft_delete(self, db_session):
        """소프트 삭제 기능을 검증합니다.

        Arrange:
            TestModel 인스턴스를 생성하고 데이터베이스에 저장합니다.
        Act:
            모델의 is_deleted 값을 True로 설정하고 저장합니다.
        Assert:
            모델의 is_deleted 값이 True로 변경되어야 합니다.
        """
        model = TestModel(name="Test Model")
        db_session.add(model)
        await db_session.flush()

        model.is_deleted = True
        await db_session.flush()

        updated_model = await db_session.get(TestModel, model.id)
        assert updated_model.is_deleted is True

    async def test_query_non_deleted(self, db_session):
        """삭제되지 않은 모델만 쿼리하는 기능을 검증합니다.

        Arrange:
            삭제된 모델과 삭제되지 않은 모델을 각각 생성합니다.
        Act:
            is_deleted가 False인 모델만 쿼리합니다.
        Assert:
            쿼리 결과에는 삭제되지 않은 모델만 포함되어야 합니다.
        """
        model1 = TestModel(name="Model 1")
        model2 = TestModel(name="Model 2", is_deleted=True)
        db_session.add_all([model1, model2])
        await db_session.flush()

        stmt = select(TestModel).where(TestModel.is_deleted == False)
        result = await db_session.execute(stmt)
        non_deleted_models = result.scalars().all()

        assert len(non_deleted_models) == 1
        assert non_deleted_models[0].name == "Model 1"

    async def test_multiple_models_with_soft_delete(self):
        """여러 모델에서 SoftDeleteMixin을 사용할 수 있는지 검증합니다.

        Arrange:
            SoftDeleteMixin을 사용하는 두 개의 다른 모델을 정의합니다.
        Act:
            두 모델의 is_deleted 속성을 검사합니다.
        Assert:
            두 모델 모두 is_deleted 속성을 가지고 있어야 합니다.
        """

        class AnotherModel(Base, SoftDeleteMixin):
            __tablename__ = "another_soft_delete_models"
            id: Mapped[int] = Column(Integer, primary_key=True)

        assert hasattr(TestModel, "is_deleted")
        assert hasattr(AnotherModel, "is_deleted")
        assert TestModel.is_deleted.property.columns[0].name == "is_deleted"
        assert AnotherModel.is_deleted.property.columns[0].name == "is_deleted"
