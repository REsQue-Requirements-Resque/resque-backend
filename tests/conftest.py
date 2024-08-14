import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.base import Base, get_async_db
from app.core.config import settings
from httpx import AsyncClient
from app.main import app
from app.models import User
from app.core.security import get_password_hash
import uuid
import ssl


@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=True, future=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_async_db():
        try:
            yield db_session
        finally:
            await db_session.close()

    app.dependency_overrides[get_async_db] = override_get_async_db

    base_url = "http://test"
    async with AsyncClient(app=app, base_url=base_url) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def httpsclient(db_session: AsyncSession):
    async def override_get_async_db():
        try:
            yield db_session
        finally:
            await db_session.close()

    app.dependency_overrides[get_async_db] = override_get_async_db

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    base_url = "https://test"
    async with AsyncClient(
        app=app, base_url=base_url, verify=ssl_context, follow_redirects=True
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def unique_email():
    return f"test_{uuid.uuid4()}@example.com"


@pytest.fixture
async def test_user(db_session: AsyncSession, unique_email):
    user = User(
        email=unique_email,
        hashed_password=get_password_hash("securePassword123!"),
        name="Test User",  # Change full_name to name if that's what your User model uses
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
