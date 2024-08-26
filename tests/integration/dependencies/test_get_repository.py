import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.get_repository import get_repository, repository_factory


@pytest.mark.asyncio
class TestGetRepository:
    class DummyRepository:
        def __init__(self, db: AsyncSession):
            self.db = db

    class AnotherDummyRepository:
        def __init__(self, db: AsyncSession):
            self.db = db

    async def test_creates_new_instance(self, db_session):
        repo = await get_repository(self.DummyRepository, db_session)
        assert isinstance(repo, self.DummyRepository)
        assert isinstance(repo.db, AsyncSession)

    async def test_returns_existing_instance(self, db_session):
        repo1 = await get_repository(self.DummyRepository, db_session)
        repo2 = await get_repository(self.DummyRepository, db_session)
        assert repo1 is repo2

    async def test_different_classes(self, db_session):
        repo1 = await get_repository(self.DummyRepository, db_session)
        repo2 = await get_repository(self.AnotherDummyRepository, db_session)
        assert isinstance(repo1, self.DummyRepository)
        assert isinstance(repo2, self.AnotherDummyRepository)
        assert repo1 is not repo2

    async def test_db_session_passed_correctly(self, db_session):
        repo = await get_repository(self.DummyRepository, db_session)
        assert isinstance(repo.db, AsyncSession)

    async def test_multiple_repositories(self, db_session):
        repo1 = await get_repository(self.DummyRepository, db_session)
        repo2 = await get_repository(self.AnotherDummyRepository, db_session)
        repo3 = await get_repository(self.DummyRepository, db_session)

        assert repo1 is repo3
        assert repo1 is not repo2
        assert all(
            isinstance(r, (self.DummyRepository, self.AnotherDummyRepository))
            for r in [repo1, repo2, repo3]
        )

    async def test_factory_reuse(self, db_session):
        repo1 = await repository_factory.get_repository(
            self.DummyRepository, db_session
        )
        repo2 = await repository_factory.get_repository(
            self.DummyRepository, db_session
        )
        assert repo1 is repo2
        assert len(repository_factory.repository_instances) == 1

    async def test_factory_multiple_classes(self, db_session):
        repo1 = await repository_factory.get_repository(
            self.DummyRepository, db_session
        )
        repo2 = await repository_factory.get_repository(
            self.AnotherDummyRepository, db_session
        )
        assert repo1 is not repo2
        assert len(repository_factory.repository_instances) == 2

    @pytest.fixture(autouse=True)
    def teardown(self):
        yield
        repository_factory.repository_instances.clear()
