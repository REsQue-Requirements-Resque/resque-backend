import pytest
from fastapi import APIRouter, HTTPException
from app.core.permissions import PermissionChecker
from app.exceptions.exceptions import PermissionDenied, PageNotFound
from app.api.endpoint_action import EndpointAction


@pytest.fixture
def mock_router(mocker):
    return mocker.Mock(spec=APIRouter)


@pytest.fixture
def mock_permission_checker(mocker):
    return mocker.patch(f"app.core.permissions.{PermissionChecker.__name__}")


@pytest.fixture
def mock_auth_service(mocker):
    return mocker.patch("app.services.authendication_service", autospec=True)


class TestEndpointAction:

    @pytest.fixture
    def mock_router(self, mocker):
        return mocker.Mock(spec=APIRouter)

    @pytest.fixture
    def endpoint_action(self, mocker):
        async def mock_func(*args, **kwargs):
            return {"message": "Success"}

        mock_permission_checker = mocker.patch("app.core.permissions.PermissionChecker")
        return EndpointAction(
            func=mock_func,
            methods=["GET"],
            response_model=dict,
            permissions=[mocker.Mock()],  # Mock the permission class
        )

    def test_register(self, endpoint_action, mock_router, mocker):
        endpoint_action.register(mock_router, "/test")
        mock_router.add_api_route.assert_called_once_with(
            "/test",
            endpoint_action.execute,
            methods=["GET"],
            response_model=dict,
            status_code=200,
            summary="",
            description="",
            dependencies=[mocker.ANY],  # Use mocker.ANY instead of ANY
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
    async def test_execute_permission_denied(self, endpoint_action, mocker):
        mock_current_user = {"id": 1}
        mock_check_permissions = mocker.patch.object(
            endpoint_action.permission_checker,
            "check_permissions",
            side_effect=PermissionDenied,
        )

        with pytest.raises(HTTPException) as exc_info:
            await endpoint_action.execute(current_user=mock_current_user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "권한이 없습니다."

    @pytest.mark.asyncio
    async def test_execute_page_not_found(self, endpoint_action, mocker):
        mock_current_user = {"id": 1}
        mocker.patch.object(endpoint_action.permission_checker, "check_permissions")
        mocker.patch.object(endpoint_action, "func", side_effect=PageNotFound)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint_action.execute(current_user=mock_current_user)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "페이지를 찾을 수 없습니다."

    @pytest.mark.asyncio
    async def test_execute_value_error(self, endpoint_action, mocker):
        mock_current_user = {"id": 1}
        mocker.patch.object(endpoint_action.permission_checker, "check_permissions")
        mocker.patch.object(
            endpoint_action, "func", side_effect=ValueError("Invalid input")
        )

        with pytest.raises(HTTPException) as exc_info:
            await endpoint_action.execute(current_user=mock_current_user)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid input"

    @pytest.mark.asyncio
    async def test_execute_internal_error(self, endpoint_action, mocker):
        mock_current_user = {"id": 1}
        mocker.patch.object(endpoint_action.permission_checker, "check_permissions")
        mocker.patch.object(
            endpoint_action, "func", side_effect=Exception("Unexpected error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await endpoint_action.execute(current_user=mock_current_user)

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "내부 서버 오류가 발생했습니다."

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
