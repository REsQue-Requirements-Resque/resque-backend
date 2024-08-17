from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.exceptions.user_exceptions import DatabaseError, DuplicateEmailError
from app.models.user import User
from app.schemas.user import UserCreate
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, User)

    async def create_user(self, user_data: UserCreate) -> User:
        try:
            if await self.check_user_existence(user_data.email):
                raise DuplicateEmailError()

            hashed_password = get_password_hash(user_data.password)
            new_user_data = user_data.dict(exclude={"password"})
            new_user_data["hashed_password"] = hashed_password

            return await self.create(new_user_data)
        except IntegrityError:
            await self.db_session.rollback()
            raise DatabaseError("An error occurred while accessing the database")
        except DuplicateEmailError:
            raise DuplicateEmailError("Email already exists")
        except Exception as e:
            await self.db_session.rollback()
            raise DatabaseError(f"An unexpected error occurred: {str(e)}")

    async def check_user_existence(self, email: str) -> bool:
        email = email.lower()
        user = await self.get_user_by_email(email)
        return user is not None

    async def get_user_by_email(self, email: str) -> User:
        stmt = select(self.model).filter(self.model.email == email.lower())
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_data: dict) -> User:
        return await self.update(user_id, user_data)
