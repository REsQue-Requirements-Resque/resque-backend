from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class Project(BaseModel):
    founder_id = Column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)

    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    founder = relationship("User", back_populates="projects")

    __table_args__ = (
        UniqueConstraint("title", "founder_id", name="unique_project_title"),
    )
