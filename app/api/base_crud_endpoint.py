"""
이 모듈은 FastAPI를 사용하여 CRUD(Create, Read, Update, Delete) 엔드포인트를 생성하기 위한 기본 클래스를 제공합니다.

주요 구성 요소:
- EndpointAction: 엔드포인트 액션을 정의하는 클래스
- BaseCrudEndpoint: CRUD 엔드포인트를 생성하기 위한 기본 클래스

이 모듈은 일반적인 CRUD 작업을 위한 엔드포인트를 쉽게 생성할 수 있도록 도와줍니다.
"""

from typing import Generic, TypeVar, Type, List, Callable, Any, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base_model import BaseModel
from app.schemas.base_schema import BaseSchema
from app.services.base_service import BaseService
from app.db.base import get_async_db

ModelType = TypeVar("ModelType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseSchema)
ServiceType = TypeVar("ServiceType", bound=BaseService)


class EndpointAction:
    """
    엔드포인트 액션을 정의하는 클래스입니다.

    이 클래스는 FastAPI 라우터에 추가될 각 엔드포인트의 설정을 캡슐화합니다.

    속성:
        func (Callable): 엔드포인트에서 실행될 함수
        methods (List[str]): 허용된 HTTP 메서드 목록
        detail (bool): 세부 정보 엔드포인트 여부
        response_model (Any): 응답 모델
        status_code (int): HTTP 상태 코드
        url_path (str): 사용자 정의 URL 경로
    """

    def __init__(
        self,
        func: Callable,
        methods: List[str],
        detail: bool = False,
        response_model: Any = None,
        status_code: int = status.HTTP_200_OK,
        url_path: str = None,
    ):
        self.func = func
        self.methods = methods
        self.detail = detail
        self.response_model = response_model
        self.status_code = status_code
        self.url_path = url_path


class BaseCrudEndpoint(Generic[ModelType, SchemaType, ServiceType]):
    """
    CRUD 엔드포인트를 생성하기 위한 기본 클래스입니다.

    이 클래스는 특정 모델 타입에 대한 CRUD 작업(생성, 읽기, 갱신, 삭제)을 구현하기 위한 기초를 제공합니다.

    제네릭 매개변수:
    ModelType: 데이터베이스 모델의 타입
    SchemaType: Pydantic 스키마의 타입
    ServiceType: 서비스 클래스의 타입

    속성:
    service_class (Type[ServiceType]): 사용할 서비스의 클래스
    schema (Type[SchemaType]): 모델에 대한 Pydantic 스키마 클래스
    """

    service_class: Type[ServiceType]
    schema: Type[SchemaType]

    def __init__(self, router: APIRouter, prefix: str):
        """
        BaseCrudEndpoint를 초기화합니다.

        매개변수:
        router (APIRouter): 엔드포인트를 추가할 FastAPI 라우터
        prefix (str): 모든 엔드포인트에 대한 URL 접두사
        """
        self.router = router
        self.prefix = prefix
        self.urls = {
            "list": f"{self.prefix}",
            "detail": f"{self.prefix}/{{id}}",
        }
        self.actions: Dict[str, EndpointAction] = {}
        self.setup_default_actions()
        self.register_routes()

    def get_service(self, db: AsyncSession = Depends(get_async_db)) -> ServiceType:
        """
        서비스 클래스의 인스턴스를 가져옵니다.

        매개변수:
        db (AsyncSession): 데이터베이스 세션

        반환값:
        ServiceType: 서비스 클래스의 인스턴스
        """
        return self.service_class(db)

    def setup_default_actions(self):
        """
        기본 CRUD 액션을 설정합니다.
        이 메서드는 list, create, retrieve, update, delete에 대한 기본 액션을 생성합니다.
        """
        self.actions = {
            "list": EndpointAction(
                self.list, ["GET"], False, List[self.schema.ResponseSchema]
            ),
            "create": EndpointAction(
                self.create,
                ["POST"],
                False,
                self.schema.ResponseSchema,
                status.HTTP_201_CREATED,
            ),
            "retrieve": EndpointAction(
                self.get, ["GET"], True, self.schema.ResponseSchema
            ),
            "update": EndpointAction(
                self.update, ["PUT"], True, self.schema.ResponseSchema
            ),
            "delete": EndpointAction(
                self.delete, ["DELETE"], True, None, status.HTTP_204_NO_CONTENT
            ),
        }

    def register_routes(self):
        """
        설정된 액션에 대한 라우트를 등록합니다.
        이 메서드는 각 액션에 대해 FastAPI 라우터에 API 라우트를 추가합니다.
        """
        for action_name, action in self.actions.items():
            if action.detail:
                base_path = self.urls["detail"]
            else:
                base_path = self.urls["list"]

            if action.url_path:
                path = f"{base_path}/{action.url_path}"
            elif action_name not in ["list", "create", "retrieve", "update", "delete"]:
                path = f"{base_path}/{action_name}"
            else:
                path = base_path

            self.router.add_api_route(
                path,
                action.func,
                methods=action.methods,
                response_model=action.response_model,
                status_code=action.status_code,
            )

    @classmethod
    def custom_action(
        cls,
        detail: bool = False,
        methods: List[str] = ["GET"],
        response_model: Any = None,
        status_code: int = status.HTTP_200_OK,
        url_path: str = None,
    ):
        """
        사용자 정의 액션을 생성하기 위한 데코레이터입니다.

        매개변수:
        detail (bool): 세부 정보 엔드포인트 여부
        methods (List[str]): 허용된 HTTP 메서드 목록
        response_model (Any): 응답 모델
        status_code (int): HTTP 상태 코드
        url_path (str): 사용자 정의 URL 경로

        반환값:
        Callable: 데코레이터 함수
        """

        def decorator(func: Callable):
            action_name = func.__name__
            cls.actions[action_name] = EndpointAction(
                func, methods, detail, response_model, status_code, url_path
            )
            return func

        return decorator

    async def create(
        self,
        obj_in: SchemaType.CreateSchema,
        service: ServiceType = Depends(get_service),
    ) -> SchemaType.ResponseSchema:
        """
        모델의 새 인스턴스를 생성합니다.

        매개변수:
        obj_in (SchemaType.CreateSchema): 새 인스턴스를 생성하기 위한 데이터
        service (ServiceType): 작업을 수행할 서비스 인스턴스

        반환값:
        SchemaType.ResponseSchema: 생성된 인스턴스
        """
        return await service.create(obj_in)

    async def get(
        self, id: int, service: ServiceType = Depends(get_service)
    ) -> SchemaType.ResponseSchema:
        """
        ID로 모델의 인스턴스를 검색합니다.

        매개변수:
        id (int): 검색할 인스턴스의 ID
        service (ServiceType): 작업을 수행할 서비스 인스턴스

        반환값:
        SchemaType.ResponseSchema: 검색된 인스턴스
        """
        return await service.get(id)

    async def update(
        self,
        id: int,
        obj_in: SchemaType.UpdateSchema,
        service: ServiceType = Depends(get_service),
    ) -> SchemaType.ResponseSchema:
        """
        모델의 인스턴스를 업데이트합니다.

        매개변수:
        id (int): 업데이트할 인스턴스의 ID
        obj_in (SchemaType.UpdateSchema): 업데이트할 데이터
        service (ServiceType): 작업을 수행할 서비스 인스턴스

        반환값:
        SchemaType.ResponseSchema: 업데이트된 인스턴스
        """
        return await service.update(id, obj_in)

    async def delete(
        self, id: int, service: ServiceType = Depends(get_service)
    ) -> None:
        """
        모델의 인스턴스를 삭제합니다.

        매개변수:
        id (int): 삭제할 인스턴스의 ID
        service (ServiceType): 작업을 수행할 서비스 인스턴스
        """
        await service.delete(id)

    async def list(
        self, service: ServiceType = Depends(get_service)
    ) -> List[SchemaType.ResponseSchema]:
        """
        모델의 모든 인스턴스 목록을 반환합니다.

        매개변수:
        service (ServiceType): 작업을 수행할 서비스 인스턴스

        반환값:
        List[SchemaType.ResponseSchema]: 모델 인스턴스의 목록
        """
        return await service.list()
