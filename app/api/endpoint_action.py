from typing import Type, List, Any, Callable, Dict, Optional, Union
from fastapi import APIRouter, status, HTTPException
from app.core.permissions import BasePermission, IsAllowAny, PermissionChecker
from app.exceptions.exceptions import PermissionDenied, PageNotFound
from app.core.logging import logger


class EndpointAction:
    """
    API 엔드포인트 액션을 정의하고 관리하는 클래스입니다.

    이 클래스는 FastAPI 라우터에 등록될 엔드포인트의 설정과 실행을 관리합니다.
    권한 검사, 예외 처리, 로깅 등의 기능을 포함합니다.

    Attributes:
        func (Callable): 엔드포인트 핸들러 함수.
        methods (List[str]): 허용된 HTTP 메서드 리스트.
        detail (bool): 상세 조회 여부.
        response_model (Optional[Any]): 응답 모델 타입.
        status_code (int): HTTP 상태 코드.
        url_path (Optional[str]): URL 경로.
        permissions (List[Type[BasePermission]]): 권한 클래스 리스트.
        summary (str): API 엔드포인트 요약.
        description (str): API 엔드포인트 설명.
        permission_checker (PermissionChecker): 권한 검사기 인스턴스.
    """

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
        """
        EndpointAction 클래스의 초기화 메서드입니다.

        Args:
            func (Callable): 엔드포인트 핸들러 함수.
            methods (List[str]): 허용된 HTTP 메서드 리스트.
            detail (bool, optional): 상세 조회 여부. 기본값은 False.
            response_model (Optional[Any], optional): 응답 모델 타입. 기본값은 None.
            status_code (int, optional): HTTP 상태 코드. 기본값은 200.
            url_path (Optional[str], optional): URL 경로. 기본값은 None.
            permissions (List[Type[BasePermission]], optional): 권한 클래스 리스트. 기본값은 [IsAllowAny].
            summary (str, optional): API 엔드포인트 요약. 기본값은 빈 문자열.
            description (str, optional): API 엔드포인트 설명. 기본값은 빈 문자열.
        """
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
        """
        엔드포인트를 FastAPI 라우터에 등록합니다.

        Args:
            router (APIRouter): FastAPI 라우터 인스턴스.
            base_path (str): 기본 URL 경로.
        """
        path = f"{base_path}/{self.url_path}" if self.url_path else base_path

        router.add_api_route(
            path,
            self.execute,
            methods=self.methods,
            response_model=self.response_model,
            status_code=self.status_code,
            summary=self.summary,
            description=self.description,
        )

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        엔드포인트 핸들러 함수를 실행하고 권한 검사 및 예외 처리를 수행합니다.

        Args:
            *args: 위치 인자.
            **kwargs: 키워드 인자.

        Returns:
            Any: 핸들러 함수의 실행 결과.

        Raises:
            HTTPException: 권한 거부, 페이지 없음, 잘못된 값, 또는 서버 오류 발생 시.
        """
        try:
            await self.check_permissions(kwargs)
            result = await self.func(*args, **kwargs)
            self.log_success(result)
            return result
        except PermissionDenied as e:
            self.log_error(e)
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        except PageNotFound as e:
            self.log_error(e)
            raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다.")
        except ValueError as e:
            self.log_error(e)
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            self.log_error(e)
            raise HTTPException(
                status_code=500, detail="내부 서버 오류가 발생했습니다."
            )

    async def check_permissions(self, kwargs: Dict[str, Any]) -> None:
        """
        권한을 검사합니다.

        Args:
            kwargs (Dict[str, Any]): 키워드 인자 딕셔너리.

        Raises:
            ValueError: 사용자 정보를 찾을 수 없는 경우.
            PermissionDenied: 권한이 거부된 경우.
        """
        user = kwargs.get("current_user")
        if not user:
            raise ValueError("사용자 정보를 찾을 수 없습니다.")

        await self.permission_checker.check_permissions(user)

        if self.detail:
            obj = kwargs.get("obj")
            if obj:
                await self.permission_checker.check_object_permissions(user, obj)

    def log_success(self, result: Any) -> None:
        """
        성공적인 작업 결과를 로깅합니다.

        Args:
            result (Any): 작업 결과.
        """
        action = self.get_action_name()
        if hasattr(result, "id"):
            logger.info(f"{action} 성공: ID {result.id}")
        else:
            logger.info(f"{action} 성공")

    def log_error(self, error: Exception) -> None:
        """
        오류 발생 시 로그를 남깁니다.

        Args:
            error (Exception): 발생한 예외.
        """
        action = self.get_action_name()
        logger.error(f"{action} 중 오류 발생: {type(error).__name__} - {str(error)}")

    def get_action_name(self) -> str:
        """
        현재 액션의 이름을 반환합니다.

        Returns:
            str: 액션 이름 (함수 이름의 첫 글자를 대문자로 변경).
        """
        return self.func.__name__.capitalize()
