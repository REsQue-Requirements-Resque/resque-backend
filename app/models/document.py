from typing import Any, List, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base_model import BaseModel
from app.models.mixins.created_model_by_user_mixin import CreatedModelByUserMixin
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
from app.models.mixins.timestamp_mixin import TimestampMixin
from app.models.user import User
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class Document(BaseModel, CreatedModelByUserMixin, SoftDeleteMixin, TimestampMixin):
    _user_class = User

    title: Mapped[str] = mapped_column(String, nullable=False)
    project_id: str = Column(Integer, ForeignKey("projects.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("title", "project_id", name="unique_document_title"),
    )
