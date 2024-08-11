import sys
from pathlib import Path

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(settings.PROJECT_ROOT)
sys.path.insert(0, str(project_root))

# 테스트용 비동기 데이터베이스 엔진 생성
test_engine = create_async_engine(settings.TEST_DATABASE_URL)
TestingAsyncSessionLocal = sessionmaker(
    class_=AsyncSession, autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(db_engine):
    async with TestingAsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session):
    from app.db.base import get_async_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_db

    from httpx import AsyncClient

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
