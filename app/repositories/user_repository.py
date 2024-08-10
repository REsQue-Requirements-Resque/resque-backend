from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.schemas.users import UserCreate
from app.exceptions.user_exceptions import DuplicateEmailError, DatabaseError
from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_user(self, user_data: UserCreate) -> User:
        try:
            if self.check_user_existence(user_data.email):
                raise DuplicateEmailError()

            hashed_password = get_password_hash(user_data.password)
            new_user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                name=user_data.name,
            )

            self.db_session.add(new_user)
            self.db_session.commit()

            return new_user
        except IntegrityError:
            self.db_session.rollback()
            raise DatabaseError("An error occurred while accessing the database")
        except DuplicateEmailError:
            self.db_session.rollback()
            raise DuplicateEmailError("Email already exists")
        except Exception as e:
            self.db_session.rollback()
            raise DatabaseError(f"An unexpected error occurred: {str(e)}")

    def check_user_existence(self, email: str) -> bool:
        email = email.lower()
        return (
            self.db_session.query(User).filter(User.email == email).first() is not None
        )

    def get_user_by_email(self, email: str) -> User:
        return self.db_session.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> User:
        return self.db_session.query(User).filter(User.id == user_id).first()

    def update_user(self, user_id: int, user_data: dict) -> User:
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            self.db_session.commit()
        return user

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if user:
            self.db_session.delete(user)
            self.db_session.commit()
            return True
        return False
