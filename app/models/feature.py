from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.models.base_model import BaseModel
from app.models.mixins.created_model_by_user_mixin import CreatedModelByUserMixin
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
from app.models.mixins.timestamp_mixin import TimestampMixin
from app.models.user import User


class Feature(BaseModel, CreatedModelByUserMixin, SoftDeleteMixin, TimestampMixin):
    _user_class = User

    name: str = Column(String, nullable=False)
    description: str = Column(String)
    domain_id: int = Column(Integer, ForeignKey("domain.id"), nullable=False)

    domain = relationship("Domain", back_populates="features")
    requirements = relationship("Requirement", back_populates="feature")
