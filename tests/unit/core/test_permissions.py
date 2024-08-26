import pytest
from fastapi import HTTPException
from app.core.permissions import (
    BasePermission,
    IsAllowAny,
    IsAuthenticated,
    IsAllowOwner,
    PermissionChecker,
)
from app.models.user import User
from app.models.mixins.created_model_by_user_mixin import CreatedModelByUserMixin
from typing import Any


class MockUser(User):
    def __init__(self, id: int):
        self.id = id


class MockObject(CreatedModelByUserMixin):
    def __init__(self, owner: User):
        self.owner = owner


class TestPermissions:
    @pytest.fixture
    def user(self):
        return MockUser(id=1)

    @pytest.fixture
    def another_user(self):
        return MockUser(id=2)

    @pytest.fixture
    def obj(self, user):
        return MockObject(owner=user)

    def test_is_allow_any(self, user, obj):
        assert IsAllowAny.has_permission(user)
        assert IsAllowAny.has_object_permission(user, obj)
        assert IsAllowAny.has_permission(None)
        assert IsAllowAny.has_object_permission(None, None)

    def test_is_authenticated(self, user, obj):
        assert IsAuthenticated.has_permission(user)
        assert IsAuthenticated.has_object_permission(user, obj)
        assert not IsAuthenticated.has_permission(None)
        assert not IsAuthenticated.has_object_permission(None, obj)

    def test_is_allow_owner(self, user, another_user, obj):
        assert IsAllowOwner.has_permission(user)
        assert IsAllowOwner.has_object_permission(user, obj)
        assert IsAllowOwner.has_permission(another_user)
        assert not IsAllowOwner.has_object_permission(another_user, obj)
        assert not IsAllowOwner.has_permission(None)
        assert not IsAllowOwner.has_object_permission(None, obj)

    @pytest.mark.asyncio
    async def test_permission_checker_success(self, user, obj):
        checker = PermissionChecker(IsAuthenticated, IsAllowOwner)
        await checker.check_permissions(user)
        await checker.check_object_permissions(user, obj)

    @pytest.mark.asyncio
    async def test_permission_checker_fail_authentication(self):
        checker = PermissionChecker(IsAuthenticated, IsAllowOwner)
        with pytest.raises(HTTPException) as exc_info:
            await checker.check_permissions(None)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_permission_checker_fail_object_permission(
        self, user, another_user, obj
    ):
        checker = PermissionChecker(IsAuthenticated, IsAllowOwner)
        with pytest.raises(HTTPException) as exc_info:
            await checker.check_object_permissions(another_user, obj)
        assert exc_info.value.status_code == 403

    def test_base_permission(self):
        class TestPermission(BasePermission):
            @staticmethod
            def has_permission(user: User) -> bool:
                return True

            @staticmethod
            def has_object_permission(user: User, obj: Any) -> bool:
                return True

        assert TestPermission.has_permission(None)
        assert TestPermission.has_object_permission(None, None)

        with pytest.raises(NotImplementedError):
            BasePermission.has_permission(None)

        with pytest.raises(NotImplementedError):
            BasePermission.has_object_permission(None, None)
