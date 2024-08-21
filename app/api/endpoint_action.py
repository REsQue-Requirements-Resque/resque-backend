from typing import Type, List, Any, Callable, Dict, Optional
from fastapi import APIRouter, status, HTTPException, Depends
from app.core.permissions import BasePermission, IsAllowAny, PermissionChecker
from app.exceptions.exceptions import PermissionDenied, PageNotFound
from app.services import authentication_service as auth_service


class EndpointAction:
    def __init__(
        self,
        func: Callable,
        methods: List[str],
        detail: bool = False,
        response_model: Optional[Any] = None,
        status_code: int = status.HTTP_200_OK,
        url_path: Optional[str] = None,
        permissions: List[Type[BasePermission]] = [IsAllowAny],
        summary: str = "",
        description: str = "",
    ) -> None:
        if not callable(func):
            raise TypeError("func must be callable")
        self.func = func
        self.methods = methods
        self.detail = detail
        self.response_model = response_model
        self.status_code = status_code
        self.url_path = url_path
        self.permissions = permissions
        self.summary = summary
        self.description = description
        self.permission_checker = PermissionChecker(*[perm() for perm in permissions])

    def register(self, router: APIRouter, base_path: str) -> None:
        path = base_path.rstrip("/") + (
            "/" + self.url_path.lstrip("/") if self.url_path else ""
        )
        router.add_api_route(
            path,
            self.execute,
            methods=self.methods,
            response_model=self.response_model,
            status_code=self.status_code,
            summary=self.summary,
            description=self.description,
            dependencies=[Depends(auth_service.get_current_user)],
        )

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        try:
            current_user = kwargs.get("current_user")
            if not current_user:
                raise ValueError("사용자 정보를 찾을 수 없습니다.")

            if self.permissions:
                await self.permission_checker.check_permissions(current_user)
                if self.detail:
                    obj = kwargs.get("obj")
                    if obj:
                        await self.permission_checker.check_object_permissions(
                            current_user, obj
                        )

            result = await self.func(*args, **kwargs)
            return result
        except PermissionDenied:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        except PageNotFound:
            raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            raise HTTPException(
                status_code=500, detail="내부 서버 오류가 발생했습니다."
            )
