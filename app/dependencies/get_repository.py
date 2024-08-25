from typing import Any, Type, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.db.base import get_async_db

Repository = Type[Any]


class RepositoryFactory:
    def __init__(self):
        self.repository_instances: Dict[Type[Repository], Repository] = {}

    def get_repository(
        self,
        repository_class: Type[Repository],
        db: AsyncSession = Depends(get_async_db),
    ) -> Repository:
        if repository_class not in self.repository_instances:
            self.repository_instances[repository_class] = repository_class(db)
        return self.repository_instances[repository_class]


repository_factory = RepositoryFactory()
get_repository = repository_factory.get_repository
