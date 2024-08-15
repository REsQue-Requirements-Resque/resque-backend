import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectUpdate


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
class TestProjectIntegration:
    PROJECT_URL = "/api/v1/projects"

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession):
        await db_session.execute(delete(User))
        await db_session.execute(delete(Project))
        await db_session.commit()

    async def create_project(
        self, async_client: AsyncClient, auth_headers: dict, project_data: dict
    ):
        response = await async_client.post(
            self.PROJECT_URL, json=project_data, headers=auth_headers
        )
        assert response.status_code == 201, f"Project creation failed: {response.text}"
        return response.json()

    async def test_project_creation(self, client: AsyncClient, auth_headers: dict):
        project_data = {
            "title": "Test Project",
            "description": "A test project",
        }
        created_project = await self.create_project(client, auth_headers, project_data)

        assert created_project["title"] == project_data["title"]
        assert created_project["description"] == project_data["description"]

    async def test_project_retrieval(self, client: AsyncClient, auth_headers: dict):
        project_data = {
            "title": "Retrieval Project",
            "description": "A project to retrieve",
        }
        created_project = await self.create_project(client, auth_headers, project_data)

        response = await client.get(
            f"{self.PROJECT_URL}/{created_project['id']}", headers=auth_headers
        )

        assert response.status_code == 200
        retrieved_project = response.json()
        assert retrieved_project["title"] == project_data["title"]
        assert retrieved_project["description"] == project_data["description"]
