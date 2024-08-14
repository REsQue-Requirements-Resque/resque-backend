import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.main import app
from app.models.project import Project
from app.models.user import User


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
@pytest.mark.req_14_project_creation
class TestProjectAPI:
    BASE_URL = "/api/v1/projects"

    @pytest.fixture(scope="class")
    async def async_client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession):
        # Clear projects table before each test
        await db_session.execute(delete(Project))
        await db_session.commit()

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession):
        user = User(
            email="testuser@example.com",
            hashed_password="hashed_password",
            name="Test User",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def test_create_project_success(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        project_data = {
            "title": "New Project",
            "description": "This is a new project",
            "founder_id": test_user.id,
        }
        response = await async_client.post(self.BASE_URL, json=project_data)

        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["title"] == project_data["title"]
        assert response.json()["description"] == project_data["description"]
        assert response.json()["founder_id"] == test_user.id

        # Verify project in database
        result = await db_session.execute(
            select(Project).filter(Project.id == response.json()["id"])
        )
        db_project = result.scalar_one_or_none()
        assert db_project is not None
        assert db_project.title == project_data["title"]

    async def test_get_project(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        # Create a project first
        project = Project(
            title="Test Project",
            description="Test Description",
            founder_id=test_user.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        response = await async_client.get(f"{self.BASE_URL}/{project.id}")

        assert response.status_code == 200
        assert response.json()["id"] == project.id
        assert response.json()["title"] == project.title

    async def test_update_project(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        # Create a project first
        project = Project(
            title="Original Title",
            description="Original Description",
            founder_id=test_user.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        update_data = {"title": "Updated Title", "description": "Updated Description"}
        response = await async_client.put(
            f"{self.BASE_URL}/{project.id}", json=update_data
        )

        assert response.status_code == 200
        assert response.json()["title"] == update_data["title"]
        assert response.json()["description"] == update_data["description"]

    async def test_delete_project(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        # Create a project first
        project = Project(
            title="Project to Delete",
            description="This will be deleted",
            founder_id=test_user.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        response = await async_client.delete(f"{self.BASE_URL}/{project.id}")

        assert response.status_code == 204

        # Verify project is deleted from database
        result = await db_session.execute(
            select(Project).filter(Project.id == project.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_list_projects(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        # Create multiple projects
        projects = [
            Project(
                title=f"Project {i}",
                description=f"Description {i}",
                founder_id=test_user.id,
            )
            for i in range(3)
        ]
        db_session.add_all(projects)
        await db_session.commit()

        response = await async_client.get(self.BASE_URL)

        assert response.status_code == 200
        assert len(response.json()) == 3
        assert all(project["founder_id"] == test_user.id for project in response.json())

    async def test_create_project_invalid_data(self, async_client: AsyncClient):
        invalid_data = {"title": "", "description": "Invalid project"}
        response = await async_client.post(self.BASE_URL, json=invalid_data)

        assert response.status_code == 422
        assert "detail" in response.json()

    def print_response(self, response):
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {response.json()}")
