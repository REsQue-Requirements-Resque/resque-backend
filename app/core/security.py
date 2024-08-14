import bcrypt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from fastapi import Depends, HTTPException, status
from app.db.base import get_async_db, AsyncSession
from app.models import User
from app.schemas.user import UserResponse
from sqlalchemy.future import select
from app.models import LoginAttempt
import logging
from sqlalchemy import delete
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


# OAuth2PasswordBearer 정의
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)
):
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

    async with db as session:
        result = await session.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return UserResponse(id=user.id, email=user.email, name=user.name)


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception


async def check_brute_force(email: str, db: AsyncSession):
    fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
    stmt = select(LoginAttempt).filter(
        LoginAttempt.email == email, LoginAttempt.attempt_time > fifteen_minutes_ago
    )
    result = await db.execute(stmt)
    attempts = result.scalars().all()

    logger.info(f"Login attempts for {email} in the last 15 minutes: {len(attempts)}")

    if len(attempts) >= 5:
        logger.warning(f"Brute force attempt detected for {email}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    # Remove old attempts
    delete_stmt = delete(LoginAttempt).where(
        LoginAttempt.email == email, LoginAttempt.attempt_time <= fifteen_minutes_ago
    )
    await db.execute(delete_stmt)

    # Record this attempt
    new_attempt = LoginAttempt(email=email)
    db.add(new_attempt)
    await db.commit()
    logger.info(f"New login attempt recorded for {email}")


async def clear_login_attempts(email: str, db: AsyncSession):
    delete_stmt = delete(LoginAttempt).where(LoginAttempt.email == email)
    await db.execute(delete_stmt)
    await db.commit()
    logger.info(f"Cleared all login attempts for {email} after successful login")
