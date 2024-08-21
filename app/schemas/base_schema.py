from pydantic import BaseModel
from typing import List, Generic, TypeVar, Optional
from datetime import datetime

T = TypeVar("T", bound=BaseModel)


class CreateSchema(BaseModel):
    """생성 작업을 위한 기본 스키마 클래스입니다.

    이 클래스는 새로운 객체를 생성할 때 사용되는 데이터의 기본 구조를 정의합니다.
    특정 모델의 생성 스키마는 이 클래스를 상속받아 구현해야 합니다.
    """

    pass


class UpdateSchema(BaseModel):
    """업데이트 작업을 위한 기본 스키마 클래스입니다.

    이 클래스는 기존 객체를 업데이트할 때 사용되는 데이터의 기본 구조를 정의합니다.
    특정 모델의 업데이트 스키마는 이 클래스를 상속받아 구현해야 합니다.

    Attributes:
        id (int): 객체의 고유 식별자입니다.
    """


class ResponseSchema(BaseModel):
    """응답을 위한 기본 스키마 클래스입니다.

    이 클래스는 API 응답의 기본 구조를 정의합니다.
    모든 응답 객체는 최소한 id 필드를 가져야 합니다.

    Attributes:
        id (int): 객체의 고유 식별자입니다.
    """

    id: int


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션된 응답을 위한 제네릭 클래스입니다.

    이 클래스는 페이지네이션된 결과를 반환할 때 사용됩니다.
    T는 페이지네이션된 항목의 타입을 나타냅니다.

    Attributes:
        items (List[T]): 현재 페이지의 항목 리스트입니다.
        total (int): 전체 항목의 수입니다.
        page (int): 현재 페이지 번호입니다.
        size (int): 페이지당 항목 수입니다.

    Example:
        >>> class UserResponse(ResponseSchema):
        ...     name: str
        ...     email: str
        >>> UserPaginatedResponse = PaginatedResponse[UserResponse]
        >>> response = UserPaginatedResponse(
        ...     items=[UserResponse(id=1, name="John", email="john@example.com")],
        ...     total=100,
        ...     page=1,
        ...     size=10
        ... )
    """

    items: List[T]
    total: int
    page: int
    size: int
