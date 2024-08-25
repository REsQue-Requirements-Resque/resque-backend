from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.soft_delete_base_repository import SoftDeleteBaseRepository

from app.models.user import User


class UserRepository(SoftDeleteBaseRepository):
    _model_class = User
