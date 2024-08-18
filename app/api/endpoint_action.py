from typing import Type, List, Any, Callable, Dict, Optional
from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.sql import select
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from cachetools import TTLCache

from app.core.permissions import BasePermission, IsAllowAny, PermissionChecker
from app.exceptions.exceptions import PermissionDenied, PageNotFound
from app.core.logging import logger
from app.core.config import settings
from app.db.base import get_async_db
from app.models import User
from app.schemas.user import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
user_cache = TTLCache(maxsize=1000, ttl=900)  # 15분 TTL의 1000개 항목 캐시


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
        path = f"{base_path}/{self.url_path}" if self.url_path else base_path

        router.add_api_route(
            path,
            self.execute,
            methods=self.methods,
            response_model=self.response_model,
            status_code=self.status_code,
            summary=self.summary,
            description=self.description,
            dependencies=[Depends(self.get_current_user)],
        )

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_async_db),
    ) -> UserResponse:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise credentials_exception

        user = user_cache.get(email)
        if user is None:
            user = await self.get_user_from_db(email, db)
            if user is None:
                raise credentials_exception
            user_cache[email] = user

        return UserResponse(id=user.id, email=user.email, name=user.name)

    async def get_user_from_db(self, email: str, db: AsyncSession) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        try:
            current_user = kwargs.get("current_user")
            if not current_user:
                raise ValueError("사용자 정보를 찾을 수 없습니다.")

            await self.check_permissions(current_user, kwargs)
            result = await self.func(*args, **kwargs)
            self.log_success(result, current_user)
            return result
        except PermissionDenied as e:
            self.log_error(e, current_user)
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        except PageNotFound as e:
            self.log_error(e, current_user)
            raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다.")
        except ValueError as e:
            self.log_error(e, current_user)
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            self.log_error(e, current_user)
            raise HTTPException(
                status_code=500, detail="내부 서버 오류가 발생했습니다."
            )

    async def check_permissions(
        self, current_user: Any, kwargs: Dict[str, Any]
    ) -> None:
        """
        권한을 검사합니다.

        Args:
            kwargs (Dict[str, Any]): 키워드 인자 딕셔너리.

        Raises:
            ValueError: 사용자 정보를 찾을 수 없는 경우.
            PermissionDenied: 권한이 거부된 경우.
        """

        await self.permission_checker.check_permissions(current_user)

        if self.detail:
            obj = kwargs.get("obj")
            if obj:
                await self.permission_checker.check_object_permissions(
                    current_user, obj
                )

    def log_success(self, result: Any, current_user: Any) -> None:
        action = self.get_action_name()
        user_id = getattr(current_user, "id", "Unknown")
        if hasattr(result, "id"):
            logger.info(f"{action} 성공: ID {result.id}, 사용자: {user_id}")
        else:
            logger.info(f"{action} 성공, 사용자: {user_id}")

    def log_error(self, error: Exception, current_user: Any) -> None:
        action = self.get_action_name()
        user_id = getattr(current_user, "id", "Unknown")
        logger.error(
            f"{action} 중 오류 발생: {type(error).__name__} - {str(error)}, 사용자: {user_id}"
        )

    def get_action_name(self) -> str:
        """
        현재 액션의 이름을 반환합니다.

        Returns:
            str: 액션 이름 (함수 이름의 첫 글자를 대문자로 변경).
        """
        return self.func.__name__.capitalize()
