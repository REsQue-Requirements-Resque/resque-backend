from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    attempt_time = Column(DateTime(timezone=True))
