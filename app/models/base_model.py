from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declared_attr
from app.db.base import Base


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + "s"
