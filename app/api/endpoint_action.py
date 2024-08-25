from typing import List, Callable, Any, Optional
from fastapi import Depends, HTTPException, status
from app.core.permissions import BasePermission


class EndpointAction:
    def __init__(
        self,
        func: Callable,
        methods: List[str],
        is_detail: bool,
        additional_path: Optional[str] = None,
        response_model: Any = None,
        status_code: int = status.HTTP_200_OK,
        permissions: List[BasePermission] = None,
        summary: Optional[str] = None,
    ):
        self.func = func
        self.methods = methods
        self.is_detail = is_detail
        self.additional_path = additional_path
        self.response_model = response_model
        self.status_code = status_code
        self.permissions = permissions or []
        self.summary = summary

    async def execute(self, *args, **kwargs):
        id = kwargs.get("id")
        current_user = kwargs.get("current_user")

        for permission in self.permissions:
            if not await permission.has_permission(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
                )
            if self.is_detail and id:
                if not await permission.has_object_permission(current_user, id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Permission denied",
                    )

        try:
            result = await self.func(*args, **kwargs)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

        return result

    def register(self, router, prefix, tags=None):
        # prefix가 이미 '/'로 시작하는지 확인
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"

        # is_detail에 따라 경로 설정
        if self.is_detail:
            path = f"{prefix}/{{id}}"
        else:
            path = prefix

        # additional_path가 있으면 추가
        if self.additional_path:
            # additional_path가 '/'로 시작하는지 확인
            if not self.additional_path.startswith("/"):
                path += "/"
            path += self.additional_path

        # 모든 메소드를 한 번에 등록
        router.add_api_route(
            path,
            self.execute,
            methods=self.methods,
            response_model=self.response_model,
            status_code=self.status_code,
            summary=self.summary,
            tags=tags,
        )
