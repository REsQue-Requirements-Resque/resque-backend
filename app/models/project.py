from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel
from app.models.mixins.soft_delete_mixin import SoftDeleteMixin
from app.models.mixins.timestamp_mixin import TimestampMixin
from app.models.mixins.created_model_by_user_mixin import CreatedModelByUserMixin
from app.models.user import User


class Project(BaseModel, CreatedModelByUserMixin, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "projects"
    _user_class = User

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String)

    __table_args__ = (
        UniqueConstraint("title", "owner_id", name="unique_project_title"),
    )
