from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
from app.db.base import Base


class User(Base, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
