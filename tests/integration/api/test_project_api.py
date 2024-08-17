import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
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

    @pytest.fixture
    def auth_headers(self, test_user: User):
        access_token = create_access_token(data={"sub": test_user.email})
        return {"Authorization": f"Bearer {access_token}"}

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession):
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
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        project_data = {
            "title": "New Project",
            "description": "This is a new project",
        }
        response = await async_client.post(
            self.BASE_URL, json=project_data, headers=auth_headers
        )

        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["title"] == project_data["title"]
        assert response.json()["description"] == project_data["description"]
        assert response.json()["founder_id"] == test_user.id

        result = await db_session.execute(
            select(Project).filter(Project.id == response.json()["id"])
        )
        db_project = result.scalar_one_or_none()
        assert db_project is not None
        assert db_project.title == project_data["title"]

    async def test_get_project(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        project = Project(
            title="Test Project",
            description="Test Description",
            founder_id=test_user.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        response = await async_client.get(
            f"{self.BASE_URL}/{project.id}", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["id"] == project.id
        assert response.json()["title"] == project.title

    async def test_update_project(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
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
            f"{self.BASE_URL}/{project.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["title"] == update_data["title"]
        assert response.json()["description"] == update_data["description"]

        await db_session.refresh(project)
        assert project.title == update_data["title"]
        assert project.description == update_data["description"]

    async def test_delete_project(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        project = Project(
            title="Project to Delete",
            description="This will be deleted",
            founder_id=test_user.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        response = await async_client.delete(
            f"{self.BASE_URL}/{project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        result = await db_session.execute(
            select(Project).filter(Project.id == project.id)
        )
        deleted_project = result.scalar_one_or_none()
        assert deleted_project is None

    async def test_list_projects(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
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

        response = await async_client.get(self.BASE_URL, headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 3
        assert all(project["founder_id"] == test_user.id for project in response_data)

        project_titles = [project["title"] for project in response_data]
        expected_titles = [f"Project {i}" for i in range(3)]
        assert set(project_titles) == set(expected_titles)

    async def test_create_project_invalid_data(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        invalid_data = {"title": "", "description": "Invalid project"}
        response = await async_client.post(
            self.BASE_URL,
            json=invalid_data,
            headers=auth_headers,
        )
        assert response.status_code == 422
        assert "Project title must be between 3 and 100 characters" in response.text

    async def test_update_project_unauthorized(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        other_user = User(
            email="other@example.com",
            hashed_password="hashed_password",
            name="Other User",
        )
        db_session.add(other_user)
        await db_session.commit()

        project = Project(
            title="Other's Project",
            description="This is not your project",
            founder_id=other_user.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        update_data = {"title": "Trying to Update"}
        response = await async_client.put(
            f"{self.BASE_URL}/{project.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    async def test_delete_project_unauthorized(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        other_user = User(
            email="other@example.com",
            hashed_password="hashed_password",
            name="Other User",
        )
        db_session.add(other_user)
        await db_session.commit()

        project = Project(
            title="Other's Project",
            description="This is not your project",
            founder_id=other_user.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        response = await async_client.delete(
            f"{self.BASE_URL}/{project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
