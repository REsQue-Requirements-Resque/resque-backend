from sqlalchemy import Integer
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from typing import Any
from pydantic import BaseModel


class BaseModel(Base):
    __abstract__ = True

    @declared_attr
    def id(cls) -> Mapped[int]:
        return mapped_column(Integer, primary_key=True, index=True)

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"

    @classmethod
    def from_schema(cls, schema: BaseModel) -> Any:
        return cls(**schema.model_dump())
