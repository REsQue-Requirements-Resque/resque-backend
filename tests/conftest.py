import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.base import Base, get_async_db
from app.core.config import settings

# 테스트용 데이터베이스 URL 사용
TEST_SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL

# SQLite URL 처리
if TEST_SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    TEST_SQLALCHEMY_DATABASE_URL = TEST_SQLALCHEMY_DATABASE_URL.replace(
        "sqlite:", "sqlite+aiosqlite:"
    )


@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(TEST_SQLALCHEMY_DATABASE_URL, echo=True, future=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session):
    from app.main import app

    async def override_get_async_db():
        try:
            yield db_session
        finally:
            await db_session.close()

    app.dependency_overrides[get_async_db] = override_get_async_db
    yield app
    app.dependency_overrides.clear()
