from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base_model import BaseModel
from app.models.mixins.created_model_by_user_mixin import CreatedModelByUserMixin
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
from app.models.mixins.timestamp_mixin import TimestampMixin
from app.utils.enums import PriorityEnum
from app.models.user import User


class Requirement(BaseModel, CreatedModelByUserMixin, SoftDeleteMixin, TimestampMixin):
    _user_class = User

    title: str = Column(String, nullable=False)
    description: str = Column(String)
    priority: PriorityEnum = Column(Enum(PriorityEnum), nullable=False)
    feature_id: int = Column(Integer, ForeignKey("feature.id"), nullable=False)

    feature = relationship("Feature", back_populates="requirements")
    tests = relationship("TestNode", back_populates="requirement")
