from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.models.base_model import BaseModel
from app.models.mixins.created_model_by_user_mixin import CreatedModelByUserMixin
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
from app.models.mixins.timestamp_mixin import TimestampMixin
from app.models.user import User


class Domain(BaseModel, CreatedModelByUserMixin, SoftDeleteMixin, TimestampMixin):
    _user_class = User

    name: str = Column(String, nullable=False)
    description: str = Column(String)
    document_id: int = Column(Integer, ForeignKey("document.id"), nullable=False)

    document = relationship("Document", back_populates="domains")
    features = relationship("Feature", back_populates="domain")
