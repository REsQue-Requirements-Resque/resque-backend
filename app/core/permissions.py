from abc import ABC, abstractmethod
from fastapi import HTTPException
from typing import Any
from app.models.user import User
from app.models.mixins.created_model_by_user_mixin import CreatedModelByUserMixin


class BasePermission(ABC):
    @abstractmethod
    async def has_permission(self, user: User) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def has_object_permission(self, user: User, obj: Any) -> bool:
        raise NotImplementedError


class IsAllowAny(BasePermission):
    async def has_permission(self, user: User) -> bool:
        return True

    async def has_object_permission(self, user: User, obj: Any) -> bool:
        return True


class IsAuthenticated(BasePermission):
    async def has_permission(self, user: User) -> bool:
        return user is not None

    async def has_permission(self, user: User) -> bool:
        return user is not None


class IsAllowOwner(BasePermission):
    async def has_permission(self, user: User, obj: CreatedModelByUserMixin) -> bool:
        if user is None or obj is None:
            return False
        return getattr(obj, "owner", None) == user


class PermissionChecker:
    def __init__(self, *permissions: BasePermission):
        self.permissions = permissions

    async def check_permissions(self, user: User):
        for permission in self.permissions:
            if not await permission.has_permission(user):
                raise HTTPException(status_code=403, detail="Permission denied")

    async def check_object_permissions(self, user: User, obj: Any):
        for permission in self.permissions:
            if not await permission.has_object_permission(user, obj):
                raise HTTPException(status_code=403, detail="Permission denied")
