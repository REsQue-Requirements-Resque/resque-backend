import pytest
from fastapi import HTTPException
from app.exceptions.exceptions import PermissionDenied, PageNotFound
from app.api.endpoint_action import EndpointAction


class TestEndpointAction:

    @pytest.fixture
    def mock_func(self, mocker):
        async def func(*args, **kwargs):
            return {"message": "Success"}

        return mocker.AsyncMock(side_effect=func)

    @pytest.fixture
    def endpoint_action(self, mocker, mock_func):
        mock_permission_class = mocker.Mock()
        return EndpointAction(
            func=mock_func,
            methods=["GET"],
            response_model=dict,
            permissions=[mock_permission_class],
        )

    @pytest.mark.parametrize(
        "methods, expected_methods",
        [
            (["GET"], ["GET"]),
            (["POST"], ["POST"]),
            (["GET", "POST"], ["GET", "POST"]),
            ([], []),  # Edge case: empty list of methods
        ],
    )
    def test_init(self, mock_func, mocker, methods, expected_methods):
        mock_permission_class = mocker.Mock()
        action = EndpointAction(
            func=mock_func, methods=methods, permissions=[mock_permission_class]
        )
        assert action.func == mock_func
        assert action.methods == expected_methods
        assert action.detail is False
        assert action.response_model is None
        assert action.status_code == 200
        assert action.url_path is None
        assert action.permissions == [mock_permission_class]
        assert action.summary == ""
        assert action.description == ""

    @pytest.mark.parametrize(
        "base_path, url_path, expected_path",
        [
            ("/api", None, "/api"),
            ("/api", "test", "/api/test"),
            ("/api/", "test", "/api/test"),
            ("/", "test", "/test"),
        ],
    )
    def test_register(
        self, endpoint_action, mocker, base_path, url_path, expected_path
    ):
        mock_router = mocker.Mock()
        endpoint_action.url_path = url_path
        endpoint_action.register(mock_router, base_path)
        mock_router.add_api_route.assert_called_once_with(
            expected_path,
            endpoint_action.execute,
            methods=["GET"],
            response_model=dict,
            status_code=200,
            summary="",
            description="",
            dependencies=[mocker.ANY],
        )

    @pytest.mark.asyncio
    async def test_execute_success(self, endpoint_action, mocker):
        mock_current_user = {"id": 1}
        mock_check_permissions = mocker.patch.object(
            endpoint_action.permission_checker, "check_permissions"
        )

        result = await endpoint_action.execute(current_user=mock_current_user)

        assert result == {"message": "Success"}
        mock_check_permissions.assert_called_once_with(mock_current_user)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception, expected_status, expected_detail",
        [
            (PermissionDenied(), 403, "권한이 없습니다."),
            (PageNotFound(), 404, "페이지를 찾을 수 없습니다."),
            (ValueError("Invalid input"), 400, "Invalid input"),
            (Exception("Unexpected error"), 500, "내부 서버 오류가 발생했습니다."),
        ],
    )
    async def test_execute_exceptions(
        self, endpoint_action, mocker, exception, expected_status, expected_detail
    ):
        mock_current_user = {"id": 1}
        mocker.patch.object(endpoint_action.permission_checker, "check_permissions")
        mocker.patch.object(endpoint_action, "func", side_effect=exception)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint_action.execute(current_user=mock_current_user)

        assert exc_info.value.status_code == expected_status
        assert exc_info.value.detail == expected_detail

    @pytest.mark.asyncio
    async def test_execute_no_current_user(self, endpoint_action):
        with pytest.raises(HTTPException) as exc_info:
            await endpoint_action.execute()

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "사용자 정보를 찾을 수 없습니다."

    @pytest.mark.asyncio
    async def test_execute_with_detail_check(self, endpoint_action, mocker):
        mock_current_user = {"id": 1}
        mock_obj = {"id": 2}
        endpoint_action.detail = True
        mock_check_permissions = mocker.patch.object(
            endpoint_action.permission_checker, "check_permissions"
        )
        mock_check_object_permissions = mocker.patch.object(
            endpoint_action.permission_checker, "check_object_permissions"
        )

        await endpoint_action.execute(current_user=mock_current_user, obj=mock_obj)

        mock_check_permissions.assert_called_once_with(mock_current_user)
        mock_check_object_permissions.assert_called_once_with(
            mock_current_user, mock_obj
        )

    @pytest.mark.asyncio
    async def test_execute_with_empty_permissions(self, mocker):
        async def mock_func(*args, **kwargs):
            return {"message": "Success"}

        endpoint_action = EndpointAction(
            func=mock_func,
            methods=["GET"],
            permissions=[],  # Edge case: empty permissions list
        )

        mock_current_user = {"id": 1}
        result = await endpoint_action.execute(current_user=mock_current_user)

        assert result == {"message": "Success"}
        # No permission checks should be called

    def test_init_with_invalid_func(self, mocker):
        with pytest.raises(TypeError):
            EndpointAction(
                func="not_a_callable",  # Edge case: invalid function
                methods=["GET"],
            )
