from unittest.mock import ANY, AsyncMock

import pytest
from fastapi import HTTPException

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService


@pytest.fixture
def mock_project_repo():
    return AsyncMock(spec=ProjectRepository)


@pytest.fixture
def project_service(mock_project_repo):
    return ProjectService(project_repo=mock_project_repo)


@pytest.mark.asyncio
class TestProjectService:
    async def test_create_project(self, project_service, mock_project_repo):
        project_data = ProjectCreate(
            title="Test Project", description="Test Description"
        )
        current_user_id = 1
        mock_project_repo.get_by_title_and_founder.return_value = None
        mock_project_repo.create.return_value = Project(
            id=1,
            title="Test Project",
            description="Test Description",
            founder_id=current_user_id,
        )

        result = await project_service.create_project(project_data, current_user_id)

        assert result.id == 1
        assert result.title == "Test Project"
        assert result.founder_id == current_user_id
        mock_project_repo.get_by_title_and_founder.assert_called_once_with(
            "Test Project", current_user_id
        )
        mock_project_repo.create.assert_called_once_with(ANY)

    async def test_create_project_duplicate(self, project_service, mock_project_repo):
        project_data = ProjectCreate(
            title="Duplicate Project", description="Test Description"
        )
        current_user_id = 1
        mock_project_repo.get_by_title_and_founder.return_value = Project(
            id=1, title="Duplicate Project", founder_id=current_user_id
        )

        with pytest.raises(HTTPException) as excinfo:
            await project_service.create_project(project_data, current_user_id)
        assert excinfo.value.status_code == 400
        assert "already exists" in str(excinfo.value.detail)

    async def test_get_project(self, project_service, mock_project_repo):
        mock_project = Project(
            id=1, title="Test Project", description="Test Description", founder_id=1
        )
        mock_project_repo.get.return_value = mock_project

        result = await project_service.get_project(1)

        assert result == mock_project
        mock_project_repo.get.assert_called_once_with(1)

    async def test_get_project_not_found(self, project_service, mock_project_repo):
        mock_project_repo.get.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await project_service.get_project(1)
        assert excinfo.value.status_code == 404

    async def test_update_project(self, project_service, mock_project_repo):
        current_user_id = 1
        existing_project = Project(
            id=1,
            title="Old Title",
            description="Old Description",
            founder_id=current_user_id,
        )
        mock_project_repo.get.return_value = existing_project
        update_data = ProjectUpdate(title="New Title", description="New Description")
        mock_project_repo.update.return_value = Project(
            id=1,
            title="New Title",
            description="New Description",
            founder_id=current_user_id,
        )

        result = await project_service.update_project(1, update_data, current_user_id)

        assert result.title == "New Title"
        assert result.description == "New Description"
        mock_project_repo.update.assert_called_once_with(1, ANY)

    async def test_update_project_not_owner(self, project_service, mock_project_repo):
        current_user_id = 1
        existing_project = Project(
            id=1, title="Old Title", description="Old Description", founder_id=2
        )
        mock_project_repo.get.return_value = existing_project
        update_data = ProjectUpdate(title="New Title")

        with pytest.raises(HTTPException) as excinfo:
            await project_service.update_project(1, update_data, current_user_id)
        assert excinfo.value.status_code == 403

    async def test_delete_project(self, project_service, mock_project_repo):
        current_user_id = 1
        existing_project = Project(
            id=1, title="Project to Delete", founder_id=current_user_id
        )
        mock_project_repo.get.return_value = existing_project
        mock_project_repo.delete.return_value = True

        result = await project_service.delete_project(1, current_user_id)

        assert result is True
        mock_project_repo.delete.assert_called_once_with(1)

    async def test_delete_project_not_owner(self, project_service, mock_project_repo):
        current_user_id = 1
        existing_project = Project(id=1, title="Project to Delete", founder_id=2)
        mock_project_repo.get.return_value = existing_project

        with pytest.raises(HTTPException) as excinfo:
            await project_service.delete_project(1, current_user_id)
        assert excinfo.value.status_code == 403

    async def test_list_projects(self, project_service, mock_project_repo):
        mock_projects = [
            Project(id=1, title="Project 1", founder_id=1),
            Project(id=2, title="Project 2", founder_id=2),
        ]
        mock_project_repo.list.return_value = mock_projects

        result = await project_service.list_projects()

        assert result == mock_projects
        mock_project_repo.list.assert_called_once()

    async def test_get_project_by_title_and_founder(
        self, project_service, mock_project_repo
    ):
        mock_project = Project(id=1, title="Test Project", founder_id=1)
        mock_project_repo.get_by_title_and_founder.return_value = mock_project

        result = await project_service.get_project_by_title_and_founder(
            "Test Project", 1
        )

        assert result == mock_project
        mock_project_repo.get_by_title_and_founder.assert_called_once_with(
            "Test Project", 1
        )

    async def test_list_projects_by_founder(self, project_service, mock_project_repo):
        mock_projects = [
            Project(id=1, title="Project 1", founder_id=1),
            Project(id=2, title="Project 2", founder_id=1),
        ]
        mock_project_repo.list_by_founder.return_value = mock_projects

        result = await project_service.list_projects_by_founder(1)

        assert result == mock_projects
        mock_project_repo.list_by_founder.assert_called_once_with(1)
