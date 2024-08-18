from abc import ABC
from typing import Type, List, Any, Callable, Optional, Generic, TypeVar
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.models.base_model import BaseModel as DBBaseModel
from app.services.base_service import BaseService
from app.db.base import get_async_db
from app.core.permissions import BasePermission, IsAllowAny
from app.exceptions.exceptions import PermissionDenied, PageNotFound
from app.schemas.base_schema import (
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
    PaginatedResponse,
)
from app.core.logging import logger
from app.api.endpoint_action import EndpointAction

T = TypeVar("T", bound=DBBaseModel)
CreateSchemaT = TypeVar("CreateSchemaT", bound=CreateSchema)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=UpdateSchema)
ResponseSchemaT = TypeVar("ResponseSchemaT", bound=ResponseSchema)
ServiceT = TypeVar("ServiceT", bound=BaseService)


class BaseCrudEndpoint(
    ABC, Generic[T, CreateSchemaT, UpdateSchemaT, ResponseSchemaT, ServiceT]
):
    """CRUD 작업을 위한 기본 엔드포인트 클래스입니다.

    이 클래스는 기본적인 CRUD 작업에 대한 엔드포인트를 제공합니다.
    각 CRUD 작업은 데코레이터를 통해 FastAPI 라우터에 등록됩니다.

    Attributes:
        endpoint_actions (List[EndpointAction]): 등록된 엔드포인트 액션 목록.
    """

    endpoint_actions: List[EndpointAction] = []

    @classmethod
    def endpoint_action(cls, *args, **kwargs):
        """엔드포인트 액션을 정의하는 데코레이터입니다.

        이 데코레이터는 메서드를 EndpointAction으로 래핑하고 endpoint_actions 리스트에 추가합니다.

        Args:
            *args: EndpointAction 생성자에 전달될 위치 인자.
            **kwargs: EndpointAction 생성자에 전달될 키워드 인자.

        Returns:
            Callable: 데코레이터 함수.
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
        service: Type[ServiceT],
        model: Type[T],
        create_schema: Type[CreateSchemaT],
        update_schema: Type[UpdateSchemaT],
        response_schema: Type[ResponseSchemaT],
    ):
        """BaseCrudEndpoint 클래스를 초기화합니다.

        Args:
            router (APIRouter): FastAPI 라우터 인스턴스.
            prefix (str): 엔드포인트 URL 접두사.
            service (Type[ServiceT]): 서비스 클래스.
            model (Type[T]): 모델 클래스.
            create_schema (Type[CreateSchemaT]): 생성 스키마 클래스.
            update_schema (Type[UpdateSchemaT]): 업데이트 스키마 클래스.
            response_schema (Type[ResponseSchemaT]): 응답 스키마 클래스.
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
            action.register(self.router, base_path)

    @classmethod
    def get_service(cls, db: AsyncSession = Depends(get_async_db)) -> ServiceT:
        """데이터베이스 세션을 이용하여 서비스 인스턴스를 생성합니다.

        Args:
            db (AsyncSession): 비동기 데이터베이스 세션.

        Returns:
            ServiceT: 서비스 인스턴스.
        """
        return cls.service(db)

    @endpoint_action(
        methods=["POST"],
        response_model=ResponseSchemaT,
        status_code=201,
        summary="새 항목 생성",
        description="제공된 데이터로 새로운 항목을 생성합니다.",
    )
    async def create(
        self, obj_in: CreateSchemaT, service: ServiceT = Depends(get_service)
    ) -> ResponseSchemaT:
        """새로운 항목을 생성합니다.

        Args:
            obj_in (CreateSchemaT): 생성할 항목 데이터.
            service (ServiceT): 서비스 인스턴스.

        Returns:
            ResponseSchemaT: 생성된 항목 데이터.
        """
        result = await service.create(obj_in)
        logger.info(f"새 항목 생성: {result.id}")
        return result

    @endpoint_action(
        methods=["GET"],
        response_model=ResponseSchemaT,
        summary="ID로 항목 조회",
        description="특정 ID를 가진 항목을 조회합니다.",
        detail=True,
    )
    async def get(
        self, id: int, service: ServiceT = Depends(get_service)
    ) -> ResponseSchemaT:
        """ID를 이용하여 특정 항목을 조회합니다.

        Args:
            id (int): 조회할 항목의 ID.
            service (ServiceT): 서비스 인스턴스.

        Returns:
            ResponseSchemaT: 조회된 항목 데이터.

        Raises:
            PageNotFound: 항목을 찾을 수 없는 경우.
        """
        result = await service.get(id)
        if not result:
            raise PageNotFound("항목을 찾을 수 없습니다")
        return result

    @endpoint_action(
        methods=["PUT"],
        response_model=ResponseSchemaT,
        summary="항목 수정",
        description="특정 ID를 가진 항목을 수정합니다.",
        detail=True,
    )
    async def update(
        self,
        id: int,
        obj_in: UpdateSchemaT,
        service: ServiceT = Depends(get_service),
    ) -> ResponseSchemaT:
        """특정 항목을 수정합니다.

        Args:
            id (int): 수정할 항목의 ID.
            obj_in (UpdateSchemaT): 수정할 데이터.
            service (ServiceT): 서비스 인스턴스.

        Returns:
            ResponseSchemaT: 수정된 항목 데이터.
        """
        result = await service.update(id, obj_in)
        logger.info(f"항목 수정: {id}")
        return result

    @endpoint_action(
        methods=["DELETE"],
        status_code=204,
        summary="항목 삭제",
        description="특정 ID를 가진 항목을 삭제합니다.",
        detail=True,
    )
    async def delete(self, id: int, service: ServiceT = Depends(get_service)) -> None:
        """특정 항목을 삭제합니다.

        Args:
            id (int): 삭제할 항목의 ID.
            service (ServiceT): 서비스 인스턴스.
        """
        await service.delete(id)
        logger.info(f"항목 삭제: {id}")

    @endpoint_action(
        methods=["GET"],
        response_model=PaginatedResponse,
        summary="항목 목록 조회",
        description="페이지네이션, 정렬, 필터링 옵션을 사용하여 항목 목록을 조회합니다.",
    )
    async def list(
        self,
        service: ServiceT = Depends(get_service),
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        sort_by: Optional[str] = Query(None),
        filter_by: Optional[str] = Query(None),
    ) -> PaginatedResponse:
        """항목 목록을 조회합니다.

        Args:
            service (ServiceT): 서비스 인스턴스.
            page (int): 페이지 번호.
            size (int): 페이지 크기.
            sort_by (Optional[str]): 정렬 기준.
            filter_by (Optional[str]): 필터링 기준.

        Returns:
            PaginatedResponse: 페이지네이션된 항목 목록.
        """
        skip = (page - 1) * size
        items, total = await service.list(
            skip=skip, limit=size, sort_by=sort_by, filter_by=filter_by
        )
        logger.info(
            f"항목 목록 조회: page={page}, size={size}, sort_by={sort_by}, filter_by={filter_by}"
        )
        return PaginatedResponse(items=items, total=total, page=page, size=size)
