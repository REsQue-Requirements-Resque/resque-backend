from typing import List, Any, Type
from fastapi import APIRouter, Depends, Query, status

from app.db.base import get_async_db
from app.exceptions.exceptions import PageNotFound
from app.schemas.base_schema import (
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
    PaginatedResponse,
)
from app.services.base_service import BaseService
from app.core.permissions import (
    IsAuthenticated,
    IsAllowOwner,
)
from app.api.endpoint_action import EndpointAction
from app.dependencies.get_service import get_service
from app.dependencies.get_user import get_current_user


class BaseCrudEndpoint:
    prefix: str = ""
    tags: List[str] = []
    _service_cls: Type[BaseService] = None
    create_schema: Type[CreateSchema] = None
    update_schema: Type[UpdateSchema] = None
    response_schema: Type[ResponseSchema] = None

    def __init__(self, router: APIRouter):
        self.router = router
        self.service = Depends(get_service(self._service_cls))
        self.register_default_routes()
        self.register_custom_actions()

    def register_default_routes(self):
        item_name = self.prefix.rstrip("s").lstrip("/")

        base_actions = {
            "create": EndpointAction(
                func=self.create,
                methods=["POST"],
                is_detail=False,
                response_model=self.response_schema,
                status_code=status.HTTP_201_CREATED,
                permissions=[IsAuthenticated],
                summary=f"Create new {item_name}",
            ),
            "list": EndpointAction(
                func=self.list,
                methods=["GET"],
                is_detail=False,
                response_model=PaginatedResponse[self.response_schema],
                permissions=[IsAuthenticated],
                summary=f"List all {item_name}s",
            ),
            "retrieve": EndpointAction(
                func=self.retrieve,
                methods=["GET"],
                is_detail=True,
                response_model=self.response_schema,
                permissions=[IsAuthenticated],
                summary=f"Retrieve specific {item_name}",
            ),
            "update": EndpointAction(
                func=self.update,
                methods=["PUT"],
                is_detail=True,
                response_model=self.response_schema,
                permissions=[IsAuthenticated, IsAllowOwner],
                summary=f"Update {item_name}",
            ),
            "delete": EndpointAction(
                func=self.delete,
                methods=["DELETE"],
                is_detail=True,
                status_code=status.HTTP_204_NO_CONTENT,
                permissions=[IsAuthenticated, IsAllowOwner],
                summary=f"Delete {item_name}",
            ),
        }

        for action_name, action in base_actions.items():
            action.register(self.router, self.prefix, self.tags)

    def register_custom_actions(self):
        pass

    async def create(
        self, data: CreateSchema, current_user: Any = Depends(get_current_user)
    ) -> Any:
        return await self.service.create(data, current_user)

    async def list(
        self,
        current_user: Any = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
    ) -> PaginatedResponse[Any]:
        items, total = await self.service.list(current_user, page, page_size)
        return PaginatedResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    async def retrieve(
        self, id: int, current_user: Any = Depends(get_current_user)
    ) -> Any:
        item = await self.service.get(id)
        if not item:
            raise PageNotFound(f"Item with id {id} not found")
        return item

    async def update(
        self, id: int, data: UpdateSchema, current_user: Any = Depends(get_current_user)
    ) -> Any:
        updated_item = await self.service.update(id, data, current_user)
        if not updated_item:
            raise PageNotFound(f"Item with id {id} not found")
        return updated_item

    async def delete(
        self, id: int, current_user: Any = Depends(get_current_user)
    ) -> None:
        deleted = await self.service.delete(id, current_user)
        if not deleted:
            raise PageNotFound(f"Item with id {id} not found")
