import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.project_repository import ProjectRepository
from app.models.project import Project
from app.models.user import User
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
class TestProjectRepository:
    @pytest.fixture
    async def project_repo(self, db_session: AsyncSession):
        return ProjectRepository(db_session)

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession):
        user = User(email="test@example.com", hashed_password="hashed_password")
        db_session.add(user)
        await db_session.commit()
        return user

    async def test_create_project(
        self, project_repo: ProjectRepository, test_user: User
    ):
        project_data = {
            "title": "Test Project",
            "description": "This is a test project",
            "founder_id": test_user.id,
        }
        project = await project_repo.create(Project(**project_data))
        assert project.id is not None
        assert project.title == project_data["title"]
        assert project.description == project_data["description"]
        assert project.founder_id == test_user.id

    async def test_get_project(self, project_repo: ProjectRepository, test_user: User):
        project_data = {
            "title": "Project to Get",
            "description": "This project will be retrieved",
            "founder_id": test_user.id,
        }
        created_project = await project_repo.create(Project(**project_data))
        retrieved_project = await project_repo.get(created_project.id)
        assert retrieved_project is not None
        assert retrieved_project.id == created_project.id
        assert retrieved_project.title == project_data["title"]

    async def test_list_projects(
        self, project_repo: ProjectRepository, test_user: User
    ):
        project_data_list = [
            {
                "title": "Project 1",
                "description": "Description 1",
                "founder_id": test_user.id,
            },
            {
                "title": "Project 2",
                "description": "Description 2",
                "founder_id": test_user.id,
            },
            {
                "title": "Project 3",
                "description": "Description 3",
                "founder_id": test_user.id,
            },
        ]
        for data in project_data_list:
            await project_repo.create(Project(**data))

        projects = await project_repo.list()
        assert len(projects) >= 3  # 기존 프로젝트가 있을 수 있으므로 '>=' 사용
        assert all(isinstance(p, Project) for p in projects)

    async def test_update_project(
        self, project_repo: ProjectRepository, test_user: User
    ):
        project_data = {
            "title": "Initial Title",
            "description": "Initial description",
            "founder_id": test_user.id,
        }
        project = await project_repo.create(Project(**project_data))

        updated_data = {"title": "Updated Title", "description": "Updated description"}
        updated_project = await project_repo.update(project.id, updated_data)
        assert updated_project.title == updated_data["title"]
        assert updated_project.description == updated_data["description"]

    async def test_delete_project(
        self, project_repo: ProjectRepository, test_user: User
    ):
        project_data = {
            "title": "Project to Delete",
            "description": "This project will be deleted",
            "founder_id": test_user.id,
        }
        project = await project_repo.create(Project(**project_data))

        await project_repo.delete(project.id)
        deleted_project = await project_repo.get(project.id)
        assert deleted_project is None

    async def test_project_founder_relationship(
        self, project_repo: ProjectRepository, test_user: User, db_session: AsyncSession
    ):
        project_data = {
            "title": "Relationship Test Project",
            "description": "Testing relationship",
            "founder_id": test_user.id,
        }
        project = await project_repo.create(Project(**project_data))

        # Refresh the session to ensure we have the latest data
        await db_session.refresh(project)

        assert project.founder_id == test_user.id
        assert project.founder.email == test_user.email

    async def test_create_project_with_duplicate_title(
        self, project_repo: ProjectRepository, test_user: User
    ):
        project_data = {
            "title": "Duplicate Title",
            "description": "This title will be duplicated",
            "founder_id": test_user.id,
        }
        await project_repo.create(Project(**project_data))

        with pytest.raises(IntegrityError):
            await project_repo.create(Project(**project_data))
