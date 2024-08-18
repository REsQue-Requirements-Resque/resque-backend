from abc import ABC
from typing import Type, List, Any, Callable, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base_model import BaseModel
from app.services.base_service import BaseService
from app.db.base import get_async_db
from app.core.permissions import BasePermission, IsAllowAny
from app.schemas.base_schema import CreateSchema, UpdateSchema, ResponseSchema
from app.core.logging import logger


class EndpointAction:
    """API 엔드포인트 액션을 정의하는 클래스입니다.

    이 클래스는 FastAPI 라우터에 등록될 엔드포인트의 메타데이터를 포함합니다.

    Attributes:
        func (Callable): 엔드포인트 핸들러 함수
        methods (List[str]): 허용된 HTTP 메서드 리스트
        detail (bool): 상세 뷰 여부
        response_model (Any): 응답 모델
        status_code (int): HTTP 상태 코드
        url_path (str): URL 경로
        permissions (List[Type[BasePermission]]): 권한 체크 리스트
        summary (str): API 요약
        description (str): API 상세 설명
    """

    def __init__(
        self,
        func: Callable,
        methods: List[str],
        detail: bool = False,
        response_model: Any = None,
        status_code: int = status.HTTP_200_OK,
        url_path: str = None,
        permissions: List[Type[BasePermission]] = [IsAllowAny],
        summary: str = "",
        description: str = "",
    ):
        self.func = func
        self.methods = methods
        self.detail = detail
        self.response_model = response_model
        self.status_code = status_code
        self.url_path = url_path
        self.permissions = permissions
        self.summary = summary
        self.description = description


class BaseCrudEndpoint(ABC):
    """CRUD 작업을 위한 기본 엔드포인트 클래스입니다.

    이 클래스는 생성, 조회, 수정, 삭제 등의 기본적인 CRUD 작업을 위한
    엔드포인트를 자동으로 생성합니다.

    Attributes:
        endpoint_actions (List[EndpointAction]): 등록된 엔드포인트 액션 리스트
    """

    endpoint_actions: List[EndpointAction] = []

    @classmethod
    def endpoint_action(cls, *args, **kwargs):
        """엔드포인트 액션을 정의하는 데코레이터입니다.

        이 데코레이터를 사용하여 CRUD 메서드에 대한 라우팅 정보를 정의합니다.

        Returns:
            Callable: 데코레이터 함수
        """

        def decorator(func: Callable):
            action = EndpointAction(func=func, *args, **kwargs)
            cls.endpoint_actions.append(action)
            return func

        return decorator

    def __init__(
        self,
        router: APIRouter,
        prefix: str,
        service: Type[BaseService],
        model: Type[BaseModel],
        create_schema: Type[CreateSchema],
        update_schema: Type[UpdateSchema],
        response_schema: Type[ResponseSchema],
    ):
        """BaseCrudEndpoint 클래스를 초기화합니다.

        Args:
            router: FastAPI 라우터 객체
            prefix: API 엔드포인트의 접두사
            service: CRUD 작업을 수행할 서비스 클래스
            model: 데이터베이스 모델 클래스
            create_schema: 생성 요청을 위한 Pydantic 스키마
            update_schema: 수정 요청을 위한 Pydantic 스키마
            response_schema: 응답을 위한 Pydantic 스키마
        """
        self.router = router
        self.prefix = prefix
        self.service = service
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.urls = {
            "list": f"{self.prefix}",
            "detail": f"{self.prefix}/{{id}}",
        }
        self.register_routes()

    def register_routes(self):
        """정의된 엔드포인트 액션들을 FastAPI 라우터에 등록합니다."""
        for action in self.endpoint_actions:
            if action.detail:
                base_path = self.urls["detail"]
            else:
                base_path = self.urls["list"]

            path = f"{base_path}/{action.url_path}" if action.url_path else base_path

            dependencies = [Depends(permission()) for permission in action.permissions]

            self.router.add_api_route(
                path,
                action.func.__get__(self),
                methods=action.methods,
                response_model=action.response_model,
                status_code=action.status_code,
                dependencies=dependencies,
                summary=action.summary,
                description=action.description,
            )

    def get_service(self, db: AsyncSession = Depends(get_async_db)) -> BaseService:
        """데이터베이스 세션을 이용하여 서비스 인스턴스를 생성합니다.

        Args:
            db: 데이터베이스 세션

        Returns:
            서비스 인스턴스
        """
        return self.service(db)

    @endpoint_action(
        ["POST"],
        response_model=ResponseSchema,
        status_code=status.HTTP_201_CREATED,
        summary="새 항목 생성",
        description="제공된 데이터로 새로운 항목을 생성합니다.",
    )
    async def create(
        self, obj_in: CreateSchema, service: BaseService = Depends(get_service)
    ) -> ResponseSchema:
        """새로운 항목을 생성합니다.

        Args:
            obj_in: 생성할 항목의 데이터
            service: CRUD 작업을 수행할 서비스 인스턴스

        Returns:
            생성된 항목의 정보

        Raises:
            HTTPException: 항목 생성 중 오류 발생 시
        """
        try:
            result = await service.create(obj_in)
            logger.info(f"새 항목 생성: {result.id}")
            return result
        except Exception as e:
            logger.error(f"항목 생성 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    @endpoint_action(
        ["GET"],
        detail=True,
        response_model=ResponseSchema,
        summary="ID로 항목 조회",
        description="특정 ID를 가진 항목을 조회합니다.",
    )
    async def get(
        self, id: int, service: BaseService = Depends(get_service)
    ) -> ResponseSchema:
        """ID를 이용하여 특정 항목을 조회합니다.

        Args:
            id: 조회할 항목의 ID
            service: CRUD 작업을 수행할 서비스 인스턴스

        Returns:
            조회된 항목의 정보

        Raises:
            HTTPException: 항목을 찾을 수 없거나 조회 중 오류 발생 시
        """
        try:
            result = await service.get(id)
            if not result:
                raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다")
            return result
        except Exception as e:
            logger.error(f"항목 {id} 조회 중 오류 발생: {str(e)}")
            raise

    @endpoint_action(
        ["GET"],
        response_model=List[ResponseSchema],
        summary="항목 목록 조회",
        description="페이지네이션, 정렬, 필터링 옵션을 사용하여 항목 목록을 조회합니다.",
    )
    async def list(
        self,
        service: BaseService = Depends(get_service),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        sort_by: Optional[str] = Query(None),
        filter_by: Optional[str] = Query(None),
    ) -> List[ResponseSchema]:
        """항목 목록을 조회합니다.

        Args:
            service: CRUD 작업을 수행할 서비스 인스턴스
            skip: 건너뛸 항목의 수
            limit: 반환할 최대 항목 수
            sort_by: 정렬 기준
            filter_by: 필터링 기준

        Returns:
            조회된 항목 목록

        Raises:
            HTTPException: 목록 조회 중 오류 발생 시
        """
        try:
            result = await service.list(
                skip=skip, limit=limit, sort_by=sort_by, filter_by=filter_by
            )
            logger.info(
                f"항목 목록 조회: skip={skip}, limit={limit}, sort_by={sort_by}, filter_by={filter_by}"
            )
            return result
        except Exception as e:
            logger.error(f"항목 목록 조회 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    @endpoint_action(
        ["PUT"],
        detail=True,
        response_model=ResponseSchema,
        summary="항목 수정",
        description="특정 ID를 가진 항목을 수정합니다.",
    )
    async def update(
        self, id: int, obj_in: UpdateSchema, service: BaseService = Depends(get_service)
    ) -> ResponseSchema:
        """특정 항목을 수정합니다.

        Args:
            id: 수정할 항목의 ID
            obj_in: 수정할 데이터
            service: CRUD 작업을 수행할 서비스 인스턴스

        Returns:
            수정된 항목의 정보

        Raises:
            HTTPException: 항목 수정 중 오류 발생 시
        """
        try:
            result = await service.update(id, obj_in)
            logger.info(f"항목 수정: {id}")
            return result
        except Exception as e:
            logger.error(f"항목 {id} 수정 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    @endpoint_action(
        ["DELETE"],
        detail=True,
        status_code=status.HTTP_204_NO_CONTENT,
        summary="항목 삭제",
        description="특정 ID를 가진 항목을 삭제합니다.",
    )
    async def delete(
        self, id: int, service: BaseService = Depends(get_service)
    ) -> None:
        """특정 항목을 삭제합니다.

        Args:
            id: 삭제할 항목의 ID
            service: CRUD 작업을 수행할 서비스 인스턴스

        Raises:
            HTTPException: 항목 삭제 중 오류 발생 시
        """
        try:
            await service.delete(id)
            logger.info(f"항목 삭제: {id}")
        except Exception as e:
            logger.error(f"항목 {id} 삭제 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
