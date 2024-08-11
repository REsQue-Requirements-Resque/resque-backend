from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.exceptions.user_exceptions import DuplicateEmailError, DatabaseError
from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(self, user_data: UserCreate) -> User:
        try:
            if await self.check_user_existence(user_data.email):
                raise DuplicateEmailError()

            hashed_password = get_password_hash(user_data.password)
            new_user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                name=user_data.name,
            )

            self.db_session.add(new_user)
            await self.db_session.commit()
            await self.db_session.refresh(new_user)

            return new_user
        except IntegrityError:
            await self.db_session.rollback()
            raise DatabaseError("An error occurred while accessing the database")
        except DuplicateEmailError:
            await self.db_session.rollback()
            raise DuplicateEmailError("Email already exists")
        except Exception as e:
            await self.db_session.rollback()
            raise DatabaseError(f"An unexpected error occurred: {str(e)}")

    async def check_user_existence(self, email: str) -> bool:
        email = email.lower()
        result = await self.db_session.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none() is not None

    async def get_user_by_email(self, email: str) -> User:
        result = await self.db_session.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User:
        result = await self.db_session.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_data: dict) -> User:
        user = await self.get_user_by_id(user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            await self.db_session.commit()
            await self.db_session.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user_by_id(user_id)
        if user:
            await self.db_session.delete(user)
            await self.db_session.commit()
            return True
        return False
