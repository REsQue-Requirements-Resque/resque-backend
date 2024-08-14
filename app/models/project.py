from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    founder_id = Column(Integer, ForeignKey("users.id"), index=True)
    is_deleted = Column(Integer, default=0)

    # Relationship
    founder = relationship("User", back_populates="projects")
