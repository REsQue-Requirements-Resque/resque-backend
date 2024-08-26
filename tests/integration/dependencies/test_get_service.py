import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.get_service import ServiceFactory, get_service
from app.dependencies.get_repository import get_repository, RepositoryFactory


class DummyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


@pytest.mark.asyncio
class TestGetService:
    class DummyService:
        repository = DummyRepository

        def __init__(self, repository):
            self.repository = repository

    class AnotherDummyService:
        repository = DummyRepository

        def __init__(self, repository):
            self.repository = repository

    class ServiceWithoutRepository:
        def __init__(self):
            pass

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # 각 테스트 전에 ServiceFactory와 RepositoryFactory를 초기화합니다
        ServiceFactory().service_instances.clear()
        RepositoryFactory().repository_instances.clear()

    async def test_creates_new_instance(self, db_session):
        service = await get_service(self.DummyService)
        assert isinstance(service, self.DummyService)
        assert isinstance(service.repository, DummyRepository)

    async def test_returns_existing_instance(self, db_session):
        service1 = await get_service(self.DummyService)
        service2 = await get_service(self.DummyService)
        assert service1 is service2

    async def test_different_classes(self, db_session):
        service1 = await get_service(self.DummyService)
        service2 = await get_service(self.AnotherDummyService)
        assert isinstance(service1, self.DummyService)
        assert isinstance(service2, self.AnotherDummyService)
        assert service1 is not service2

    async def test_repository_passed_correctly(self, db_session):
        service = await get_service(self.DummyService)
        assert isinstance(service.repository, DummyRepository)

    async def test_service_without_repository_attribute(self):
        with pytest.raises(NotImplementedError):
            await get_service(self.ServiceWithoutRepository)

    async def test_multiple_services(self, db_session):
        service1 = await get_service(self.DummyService)
        service2 = await get_service(self.AnotherDummyService)
        service3 = await get_service(self.DummyService)

        assert service1 is service3
        assert service1 is not service2
        assert all(
            isinstance(s, (self.DummyService, self.AnotherDummyService))
            for s in [service1, service2, service3]
        )

    async def test_repository_reuse(self, db_session):
        service1 = await get_service(self.DummyService)
        service2 = await get_service(self.AnotherDummyService)
        assert service1.repository is service2.repository
