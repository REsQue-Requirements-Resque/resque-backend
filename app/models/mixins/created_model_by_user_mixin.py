from typing import Any, Type
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship, declared_attr, Mapped


class CreatedModelByUserMixin:
    """사용자에 의해 생성된 모델을 위한 믹스인 클래스.

    이 믹스인은 모델에 소유자(owner) 관계를 추가합니다. 소유자는 모델을 생성한 사용자를 나타냅니다.
    이 클래스를 사용하려면 _user_class 속성을 설정해야 합니다.

    Attributes:
        _user_class (Type[Any]): 사용자 모델 클래스. 이 속성은 반드시 설정되어야 합니다.
        owner_id (Mapped[int]): 소유자의 ID를 저장하는 외래 키 컬럼.
        owner (Mapped[Any]): 소유자 객체와의 관계.

    Raises:
        NotImplementedError: _user_class가 설정되지 않은 경우 발생합니다.

    Example:
        class User(Base):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            username = Column(String)

        class Post(Base, CreatedModelByUserMixin):
            __tablename__ = 'posts'
            id = Column(Integer, primary_key=True)
            title = Column(String)
            _user_class = User
    """

    _user_class: Type[Any] = None

    @declared_attr
    def owner_id(cls) -> Mapped[int]:
        """소유자 ID를 위한 외래 키 컬럼.

        Returns:
            Mapped[int]: 소유자 ID를 저장하는 컬럼.

        Raises:
            NotImplementedError: _user_class가 설정되지 않은 경우 발생합니다.
        """
        if cls._user_class is None:
            raise NotImplementedError(f"{cls.__name__} must declare _user_class")
        return Column(
            Integer,
            ForeignKey(f"{cls._user_class.__tablename__}.id"),
            nullable=False,
            index=True,
        )

    @declared_attr
    def owner(cls) -> Mapped[Any]:
        """소유자 객체와의 관계.

        Returns:
            Mapped[Any]: 소유자 객체와의 관계.

        Raises:
            NotImplementedError: _user_class가 설정되지 않은 경우 발생합니다.
        """
        if cls._user_class is None:
            raise NotImplementedError(f"{cls.__name__} must declare _user_class")
        return relationship(
            cls._user_class.__name__, back_populates=f"{cls.__tablename__}"
        )

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """서브클래스 초기화 메서드.

        이 메서드는 CreatedModelByUserMixin을 상속받는 클래스가 정의될 때 자동으로 호출됩니다.
        _user_class에 역방향 관계를 자동으로 추가합니다.

        Args:
            **kwargs: 추가 키워드 인자.
        """
        super().__init_subclass__(**kwargs)
        if cls._user_class is not None and not hasattr(
            cls._user_class, cls.__tablename__
        ):
            setattr(
                cls._user_class,
                cls.__tablename__,
                relationship(cls.__name__, back_populates="owner"),
            )
