import pytest
from fastapi import HTTPException
from app.api.endpoint_action import EndpointAction


class SimplePermission:
    @staticmethod
    async def has_permission(user):
        return user == "allowed_user"

    @staticmethod
    async def has_object_permission(user, obj):
        return obj == 1


async def simple_func(*args, **kwargs):
    return {"message": "success"}


class TestEndpointAction:
    def test_init(self):
        action = EndpointAction(
            func=simple_func,
            methods=["GET"],
            is_detail=False,
            additional_path="/test",
            response_model=dict,
            status_code=200,
            permissions=[SimplePermission()],
            summary="Test Action",
        )
        assert action.func == simple_func
        assert action.methods == ["GET"]
        assert action.is_detail == False
        assert action.additional_path == "/test"
        assert action.response_model == dict
        assert action.status_code == 200
        assert len(action.permissions) == 1
        assert isinstance(action.permissions[0], SimplePermission)
        assert action.summary == "Test Action"

    @pytest.mark.asyncio
    async def test_execute_success(self):
        action = EndpointAction(
            func=simple_func,
            methods=["GET"],
            is_detail=False,
            permissions=[SimplePermission()],
        )
        result = await action.execute(current_user="allowed_user")
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_execute_permission_denied(self):
        action = EndpointAction(
            func=simple_func,
            methods=["GET"],
            is_detail=False,
            permissions=[SimplePermission()],
        )
        with pytest.raises(HTTPException) as exc_info:
            await action.execute(current_user="disallowed_user")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_execute_detail_permission_denied(self):
        action = EndpointAction(
            func=simple_func,
            methods=["GET"],
            is_detail=True,
            permissions=[SimplePermission()],
        )
        with pytest.raises(HTTPException) as exc_info:
            await action.execute(current_user="allowed_user", id=2)
        assert exc_info.value.status_code == 403

    def test_register_path_construction(self):
        class MockRouter:
            def __init__(self):
                self.routes = []

            def add_api_route(self, path, endpoint, methods, **kwargs):
                self.routes.append((path, methods))

        # Test case 1: Non-detail route
        router = MockRouter()
        action = EndpointAction(func=simple_func, methods=["GET"], is_detail=False)
        action.register(router, "api")
        assert router.routes[0] == ("/api", ["GET"])

        # Test case 2: Detail route
        router = MockRouter()
        action = EndpointAction(func=simple_func, methods=["GET"], is_detail=True)
        action.register(router, "api")
        assert router.routes[0] == ("/api/{id}", ["GET"])

        # Test case 3: Additional path
        router = MockRouter()
        action = EndpointAction(
            func=simple_func, methods=["GET"], is_detail=False, additional_path="/extra"
        )
        action.register(router, "api")
        assert router.routes[0] == ("/api/extra", ["GET"])

        # Test case 4: Multiple methods
        router = MockRouter()
        action = EndpointAction(
            func=simple_func, methods=["GET", "POST"], is_detail=False
        )
        action.register(router, "api")
        assert router.routes[0] == ("/api", ["GET", "POST"])
