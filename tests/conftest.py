import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(settings.PROJECT_ROOT)
sys.path.insert(0, str(project_root))

# 테스트용 데이터베이스 엔진 생성
test_engine = create_engine(settings.TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    from app.db.base import get_db
    from app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # 여기서 session을 닫지 않습니다.

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient

    return TestClient(app)
