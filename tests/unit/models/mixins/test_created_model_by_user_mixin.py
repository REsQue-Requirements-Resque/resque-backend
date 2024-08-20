import pytest
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.orm.relationships import RelationshipProperty
from app.models.mixins.created_model_by_user_mixin import CreatedModelByUserMixin
from app.db.base import Base
import uuid
from sqlalchemy.future import select


class TestUser(Base):
    __tablename__ = "test_users"
    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String)


class TestModel(Base, CreatedModelByUserMixin):
    __tablename__ = "testmodels"
    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String)
    _user_class = TestUser


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.models
@pytest.mark.mixins
class TestCreatedModelByUserMixin:
    async def test_user_class_is_correctly_set(self):
        """_user_class가 올바르게 설정되었는지 검증합니다.

        Arrange:
            TestModel은 TestUser를 _user_class로 설정하여 정의되어 있습니다.
        Act:
            TestModel의 _user_class 속성을 확인합니다.
        Assert:
            _user_class가 TestUser와 동일해야 합니다.
        """
        assert (
            TestModel._user_class == TestUser
        ), "TestUser 클래스가 올바르게 설정되어야 합니다"

    async def test_tablename_is_correctly_set(self):
        """__tablename__이 올바르게 설정되었는지 검증합니다.

        Arrange:
            TestModel은 특정 __tablename__으로 정의되어 있습니다.
        Act:
            TestModel의 __tablename__ 속성을 확인합니다.
        Assert:
            __tablename__이 "testmodels"이어야 합니다.
        """
        assert (
            TestModel.__tablename__ == "testmodels"
        ), "테이블 이름이 올바르게 설정되어야 합니다"

    async def test_id_column_exists_and_is_primary_key(self):
        """id 컬럼의 존재와 기본 키 설정을 검증합니다.

        Arrange:
            TestModel은 id 컬럼이 정의되어 있습니다.
        Act:
            TestModel의 id 컬럼 속성을 검사합니다.
        Assert:
            id 컬럼이 존재하고, Column 타입이며, 기본 키로 설정되어 있어야 합니다.
        """
        assert hasattr(TestModel, "id"), "모델에 id 컬럼이 있어야 합니다"
        assert isinstance(
            TestModel.id.property.columns[0], Column
        ), "id는 Column이어야 합니다"
        assert TestModel.id.property.columns[0].primary_key, "id는 기본 키여야 합니다"

    async def test_name_column_exists(self):
        """name 컬럼의 존재를 검증합니다.

        Arrange:
            TestModel은 name 컬럼이 정의되어 있습니다.
        Act:
            TestModel의 name 컬럼 속성을 검사합니다.
        Assert:
            name 컬럼이 존재하고 Column 타입이어야 합니다.
        """
        assert hasattr(TestModel, "name"), "모델에 name 컬럼이 있어야 합니다"
        assert isinstance(
            TestModel.name.property.columns[0], Column
        ), "name은 Column이어야 합니다"

    async def test_owner_id_column_properties(self):
        """owner_id 컬럼의 속성을 검증합니다.

        Arrange:
            TestModel은 CreatedModelByUserMixin을 통해 owner_id 컬럼이 정의되어 있습니다.
        Act:
            TestModel의 owner_id 컬럼 속성을 검사합니다.
        Assert:
            owner_id 컬럼은 존재하며, Integer 타입이고, nullable이 아니며, 인덱스가 설정되어 있어야 합니다.
        """
        assert hasattr(TestModel, "owner_id"), "모델에 owner_id 컬럼이 있어야 합니다"
        owner_id_column = TestModel.owner_id.property.columns[0]
        assert isinstance(owner_id_column, Column), "owner_id는 Column이어야 합니다"
        assert owner_id_column.name == "owner_id", "컬럼 이름은 'owner_id'여야 합니다"
        assert isinstance(
            owner_id_column.type, Integer
        ), "owner_id는 Integer 타입이어야 합니다"
        assert (
            owner_id_column.nullable is False
        ), "owner_id는 nullable이 아니어야 합니다"
        assert (
            owner_id_column.index is True
        ), "owner_id는 인덱스가 설정되어 있어야 합니다"

    async def test_owner_relationship_properties(self):
        """owner 관계의 속성을 검증합니다.

        Arrange:
            TestModel은 CreatedModelByUserMixin을 통해 owner 관계가 정의되어 있습니다.
        Act:
            TestModel의 owner 관계 속성을 검사합니다.
        Assert:
            owner 관계가 존재하며, RelationshipProperty 타입이고, TestUser와 연결되어 있어야 합니다.
        """
        assert hasattr(TestModel, "owner"), "모델에 owner 관계가 있어야 합니다"
        assert isinstance(
            TestModel.owner.property, RelationshipProperty
        ), "owner는 RelationshipProperty여야 합니다"
        assert (
            TestModel.owner.property.argument == TestUser.__name__
        ), "owner는 TestUser와 관계가 있어야 합니다"

    async def test_reverse_relationship_properties(self):
        """역방향 관계의 속성을 검증합니다.

        Arrange:
            TestUser는 TestModel과의 역방향 관계가 정의되어 있습니다.
        Act:
            TestUser의 testmodels 관계 속성을 검사합니다.
        Assert:
            testmodels 관계가 존재하며, RelationshipProperty 타입이고, TestModel과 연결되어 있어야 합니다.
        """
        assert hasattr(TestUser, "testmodels"), "TestUser에 역방향 관계가 있어야 합니다"
        assert isinstance(
            TestUser.testmodels.property, RelationshipProperty
        ), "testmodels는 RelationshipProperty여야 합니다"
        assert (
            TestUser.testmodels.property.argument == TestModel.__name__
        ), "testmodels는 TestModel과 관계가 있어야 합니다"

    async def test_model_without_user_class_raises_error(self):
        """_user_class가 없는 모델 생성 시 오류 발생을 검증합니다.

        Arrange:
            _user_class가 설정되지 않은 InvalidModel을 정의합니다.
        Act:
            InvalidModel의 owner_id에 접근합니다.
        Assert:
            NotImplementedError가 발생해야 합니다.
        """
        with pytest.raises(NotImplementedError, match="must declare _user_class"):

            class InvalidModel(Base, CreatedModelByUserMixin):
                __tablename__ = "invalid_models"
                id: Mapped[int] = Column(Integer, primary_key=True)

            InvalidModel.owner_id

    async def test_model_with_none_user_class_raises_error(self):
        """_user_class가 None인 모델 생성 시 오류 발생을 검증합니다.

        Arrange:
            _user_class가 None으로 설정된 InvalidModel을 정의합니다.
        Act:
            InvalidModel의 owner_id에 접근합니다.
        Assert:
            NotImplementedError가 발생해야 합니다.
        """
        with pytest.raises(NotImplementedError, match="must declare _user_class"):

            class InvalidModel(Base, CreatedModelByUserMixin):
                __tablename__ = "invalid_models"
                id: Mapped[int] = Column(Integer, primary_key=True)
                _user_class = None

            InvalidModel.owner_id

    @pytest.mark.parametrize("invalid_user_class", ["NotAClass", 42, object()])
    async def test_invalid_user_class_raises_error(self, invalid_user_class):
        """잘못된 _user_class 설정 시 오류 발생을 검증합니다.

        Arrange:
            _user_class가 잘못된 값으로 설정된 InvalidModel을 정의합니다.
        Act:
            InvalidModel의 owner_id에 접근합니다.
        Assert:
            AttributeError 또는 TypeError가 발생해야 합니다.
        """
        with pytest.raises((AttributeError, TypeError)):

            class InvalidModel(Base, CreatedModelByUserMixin):
                __tablename__ = "invalid_models"
                id: Mapped[int] = Column(Integer, primary_key=True)
                _user_class = invalid_user_class

            InvalidModel.owner_id

    async def test_different_user_classes(self):
        """서로 다른 사용자 클래스를 사용하는 모델을 검증합니다.

        Arrange:
            새로운 사용자 클래스 AnotherUser와 이를 사용하는 AnotherModel을 정의합니다.
        Act:
            AnotherModel의 _user_class와 owner 관계를 검사합니다.
        Assert:
            AnotherModel의 _user_class가 AnotherUser이고, owner 관계가 올바르게 설정되어 있어야 합니다.
        """

        class AnotherUser(Base):
            __tablename__ = "another_users"
            id: Mapped[int] = Column(Integer, primary_key=True)

        class AnotherModel(Base, CreatedModelByUserMixin):
            __tablename__ = "another_models"
            id: Mapped[int] = Column(Integer, primary_key=True)
            _user_class = AnotherUser

        assert AnotherModel._user_class == AnotherUser
        assert AnotherModel.owner.property.argument == AnotherUser.__name__

    async def test_hierarchical_relationship(self):
        """계층적 관계를 가진 모델을 검증합니다.

        Arrange:
            자기 참조 관계를 가진 HierarchicalModel을 정의합니다.
        Act:
            HierarchicalModel의 관계 속성들을 검사합니다.
        Assert:
            HierarchicalModel이 owner, parent, children 관계를 가지고 있어야 합니다.
        """

        class HierarchicalModel(Base, CreatedModelByUserMixin):
            __tablename__ = "hierarchical_models"
            id: Mapped[int] = Column(Integer, primary_key=True)
            parent_id: Mapped[int] = Column(
                Integer, ForeignKey("hierarchical_models.id"), nullable=True
            )
            _user_class = TestUser

            parent = relationship(
                "HierarchicalModel", remote_side=[id], back_populates="children"
            )
            children = relationship("HierarchicalModel", back_populates="parent")

        assert hasattr(HierarchicalModel, "owner")
        assert hasattr(HierarchicalModel, "parent")
        assert hasattr(HierarchicalModel, "children")
        assert HierarchicalModel.owner.property.argument == TestUser.__name__
        assert HierarchicalModel.parent.property.argument == "HierarchicalModel"
        assert HierarchicalModel.children.property.argument == "HierarchicalModel"

    async def test_multiple_models_with_same_user_class(self):
        """동일한 사용자 클래스를 사용하는 여러 모델을 검증합니다.

        Arrange:
            TestUser를 사용하는 새로운 모델 AnotherModel을 동적으로 생성합니다.
        Act:
            TestUser의 관계 속성들을 검사합니다.
        Assert:
            TestUser가 testmodels와 새로 생성된 모델과의 관계를 모두 가지고 있어야 합니다.
        """
        unique_model_name = f"AnotherModel_{uuid.uuid4().hex[:8]}"
        unique_table_name = f"another_models_{uuid.uuid4().hex[:8]}"

        AnotherModel = type(
            unique_model_name,
            (Base, CreatedModelByUserMixin),
            {
                "__tablename__": unique_table_name,
                "id": Column(Integer, primary_key=True),
                "_user_class": TestUser,
            },
        )

        assert hasattr(TestUser, "testmodels")
        assert hasattr(TestUser, unique_table_name)
        assert TestUser.testmodels.property.argument == "TestModel"
        assert (
            getattr(TestUser, unique_table_name).property.argument == unique_model_name
        )

    async def test_create_and_query(self, db_session):
        """모델 생성 및 쿼리 기능을 검증합니다.

        Arrange:
            TestUser와 TestModel 인스턴스를 생성하고 데이터베이스에 저장합니다.
        Act:
            생성된 모델을 쿼리하고 관계를 확인합니다.
        Assert:
            생성된 모델이 올바르게 저장되고, 관계가 정확히 설정되어 있어야 합니다.
        """
        user = TestUser(name="Test TestUser")
        db_session.add(user)
        await db_session.flush()

        model = TestModel(name="Test Model", owner_id=user.id)
        db_session.add(model)
        await db_session.flush()

        # Query
        queried_model = await db_session.get(TestModel, model.id)
        assert queried_model is not None
        assert queried_model.name == "Test Model"
        assert queried_model.owner_id == user.id

        queried_user = await db_session.get(TestUser, user.id)
        assert queried_user is not None

        # Use select to get related models
        stmt = select(TestModel).where(TestModel.owner_id == queried_user.id)
        result = await db_session.execute(stmt)
        user_models = result.scalars().all()

        assert len(user_models) == 1
        assert user_models[0].id == model.id
