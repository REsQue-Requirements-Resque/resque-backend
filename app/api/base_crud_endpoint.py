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


class BaseCrudEndpoint(Generic[ModelType, SchemaType, ServiceType]):
    def __init__(
        self,
        router: APIRouter,
        service_class: Type[ServiceType],
        schema: Type[SchemaType],
        prefix: str,
    ):
        self.router = router
        self.service_class = service_class
        self.schema = schema
        self.prefix = prefix
        self.urls = {
            "list": f"{self.prefix}",
            "detail": f"{self.prefix}/{{id}}",
        }
        self.register_routes()

    def get_service(self, db: AsyncSession = Depends(get_async_db)) -> ServiceType:
        return self.service_class(db)

    def register_routes(self):
        self.register_cruds()
        self.register_custom_actions()

    def register_cruds(self):
        self.register_create()
        self.register_get()
        self.register_update()
        self.register_delete()
        self.register_list()

    def register_create(self):
        @self.router.post(
            self.urls["list"],
            response_model=self.schema.ResponseSchema,
            status_code=status.HTTP_201_CREATED,
        )
        async def create(
            obj_in: self.schema.CreateSchema,
            service: ServiceType = Depends(self.get_service),
        ) -> self.schema.ResponseSchema:
            return await self.create(obj_in, service)

    def register_get(self):
        @self.router.get(self.urls["detail"], response_model=self.schema.ResponseSchema)
        async def get(
            id: int, service: ServiceType = Depends(self.get_service)
        ) -> self.schema.ResponseSchema:
            return await self.get(id, service)

    def register_update(self):
        @self.router.put(self.urls["detail"], response_model=self.schema.ResponseSchema)
        async def update(
            id: int,
            obj_in: self.schema.UpdateSchema,
            service: ServiceType = Depends(self.get_service),
        ) -> self.schema.ResponseSchema:
            return await self.update(id, obj_in, service)

    def register_delete(self):
        @self.router.delete(self.urls["detail"], status_code=status.HTTP_204_NO_CONTENT)
        async def delete(
            id: int, service: ServiceType = Depends(self.get_service)
        ) -> None:
            await self.delete(id, service)

    def register_list(self):
        @self.router.get(
            self.urls["list"], response_model=List[self.schema.ResponseSchema]
        )
        async def list(
            service: ServiceType = Depends(self.get_service),
        ) -> List[self.schema.ResponseSchema]:
            return await self.list(service)

    def register_custom_actions(self):
        # This method should be overridden in child classes to add custom actions
        pass

    async def create(
        self, obj_in: SchemaType.CreateSchema, service: ServiceType
    ) -> SchemaType.ResponseSchema:
        return await service.create(obj_in)

    async def get(self, id: int, service: ServiceType) -> SchemaType.ResponseSchema:
        return await service.get(id)

    async def update(
        self, id: int, obj_in: SchemaType.UpdateSchema, service: ServiceType
    ) -> SchemaType.ResponseSchema:
        return await service.update(id, obj_in)

    async def delete(self, id: int, service: ServiceType) -> None:
        await service.delete(id)

    async def list(self, service: ServiceType) -> List[SchemaType.ResponseSchema]:
        return await service.list()

    def add_api_route(
        self,
        path: str,
        endpoint: Callable,
        methods: List[str],
        status_code: int = 200,
        response_model: Any = None,
        **kwargs: Any,
    ):
        self.router.add_api_route(
            path,
            endpoint,
            methods=methods,
            status_code=status_code,
            response_model=response_model,
            **kwargs,
        )

    def custom_action(self, detail: bool = False, methods: List[str] = ["GET"]):
        def decorator(func: Callable):
            action_name = func.__name__
            path = (
                f"{self.urls['detail']}/{action_name}"
                if detail
                else f"{self.urls['list']}/{action_name}"
            )
            self.add_api_route(path, func, methods=methods)
            return func

        return decorator
