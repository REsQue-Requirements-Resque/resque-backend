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
    service_class: Type[ServiceType]
    schema: Type[SchemaType]

    def __init__(self, router: APIRouter, prefix: str):
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
        return self.service_class(db)

    def setup_default_actions(self):
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
        return await service.create(obj_in)

    async def get(
        self, id: int, service: ServiceType = Depends(get_service)
    ) -> SchemaType.ResponseSchema:
        return await service.get(id)

    async def update(
        self,
        id: int,
        obj_in: SchemaType.UpdateSchema,
        service: ServiceType = Depends(get_service),
    ) -> SchemaType.ResponseSchema:
        return await service.update(id, obj_in)

    async def delete(
        self, id: int, service: ServiceType = Depends(get_service)
    ) -> None:
        await service.delete(id)

    async def list(
        self, service: ServiceType = Depends(get_service)
    ) -> List[SchemaType.ResponseSchema]:
        return await service.list()
