import pytest
from unittest.mock import AsyncMock, ANY
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository


@pytest.fixture
def mock_project_repo():
    return AsyncMock(spec=ProjectRepository)


@pytest.fixture
def project_service(mock_project_repo):
    return ProjectService(project_repo=mock_project_repo)


@pytest.mark.asyncio
class TestProjectService:
    async def test_create_project(self, project_service, mock_project_repo):
        # Arrange
        project_data = ProjectCreate(
            title="Test Project", description="Test Description", founder_id=1
        )
        mock_project_repo.create.return_value = Project(
            id=1, **project_data.model_dump()
        )

        # Act
        result = await project_service.create_project(project_data)

        # Assert
        assert result.id == 1
        assert result.title == "Test Project"
        assert result.description == "Test Description"
        assert result.founder_id == 1
        mock_project_repo.create.assert_called_once_with(ANY)

        # Additional assertion to check the contents of the created Project
        created_project = mock_project_repo.create.call_args[0][0]
        assert isinstance(created_project, Project)
        assert created_project.title == project_data.title
        assert created_project.description == project_data.description
        assert created_project.founder_id == project_data.founder_id

    async def test_get_project(self, project_service, mock_project_repo):
        # Arrange
        mock_project = Project(
            id=1, title="Test Project", description="Test Description", founder_id=1
        )
        mock_project_repo.get.return_value = mock_project

        # Act
        result = await project_service.get_project(1)

        # Assert
        assert result == mock_project
        mock_project_repo.get.assert_called_once_with(1)

    async def test_update_project(self, project_service, mock_project_repo):
        # Arrange
        project_update = ProjectUpdate(
            title="Updated Project", description="Updated Description"
        )
        mock_updated_project = Project(id=1, **project_update.dict(), founder_id=1)
        mock_project_repo.update.return_value = mock_updated_project

        # Act
        result = await project_service.update_project(1, project_update)

        # Assert
        assert result == mock_updated_project
        mock_project_repo.update.assert_called_once_with(
            1, project_update.dict(exclude_unset=True)
        )

    async def test_delete_project(self, project_service, mock_project_repo):
        # Arrange
        mock_project_repo.delete.return_value = True

        # Act
        result = await project_service.delete_project(1)

        # Assert
        assert result is True
        mock_project_repo.delete.assert_called_once_with(1)

    async def test_list_projects(self, project_service, mock_project_repo):
        # Arrange
        mock_projects = [
            Project(id=1, title="Project 1", description="Description 1", founder_id=1),
            Project(id=2, title="Project 2", description="Description 2", founder_id=2),
        ]
        mock_project_repo.list.return_value = mock_projects

        # Act
        result = await project_service.list_projects()

        # Assert
        assert result == mock_projects
        mock_project_repo.list.assert_called_once()

    # Add more tests as needed for other methods in ProjectService
