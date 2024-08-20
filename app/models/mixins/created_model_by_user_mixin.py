from typing import Any, Type
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship, declared_attr, Mapped


class CreatedModelByUserMixin:
    _user_class: Type[Any] = None

    @declared_attr
    def owner_id(cls) -> Mapped[int]:
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
        if cls._user_class is None:
            raise NotImplementedError(f"{cls.__name__} must declare _user_class")
        return relationship(
            cls._user_class.__name__, back_populates=f"{cls.__tablename__}"
        )

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._user_class is not None and not hasattr(
            cls._user_class, cls.__tablename__
        ):
            setattr(
                cls._user_class,
                cls.__tablename__,
                relationship(cls.__name__, back_populates="owner"),
            )
