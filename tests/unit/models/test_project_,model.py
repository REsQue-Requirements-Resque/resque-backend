from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.user import User


@pytest.mark.asyncio
class TestProjectModel:
    async def test_create_project(self, db_session):
        # First, create a user
        user = User(email="test@example.com", hashed_password="hashed_password")
        db_session.add(user)
        await db_session.commit()

        # Now create a project
        project = Project(
            title="Test Project",
            description="This is a test project",
            founder_id=user.id,
        )
        db_session.add(project)
        await db_session.commit()

        assert project.id is not None
        assert project.title == "Test Project"
        assert project.description == "This is a test project"
        assert project.founder_id == user.id
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

        # Test the relationship
        await db_session.refresh(user, ["projects"])
        assert project.founder == user
        assert project in user.projects

        # Alternative way to test relationship using explicit loading
        stmt = (
            select(User).options(selectinload(User.projects)).where(User.id == user.id)
        )
        result = await db_session.execute(stmt)
        loaded_user = result.scalar_one()
        assert project in loaded_user.projects

    async def test_project_title_unique(self, db_session):
        # 프로젝트 제목 유일성 테스트
        project1 = Project(title="Unique Project", founder_id=1)
        db_session.add(project1)
        await db_session.commit()

        project2 = Project(title="Unique Project", founder_id=1)
        db_session.add(project2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_project_founder_relationship(self, db_session):
        # 프로젝트와 창립자(User) 관계 테스트
        user = User(email="test@example.com", hashed_password="hashed_password")
        db_session.add(user)
        await db_session.commit()

        project = Project(title="Relationship Test Project", founder_id=user.id)
        db_session.add(project)
        await db_session.commit()

        assert project.founder_id == user.id
        # founder 관계가 제대로 설정되었는지 확인
        assert project.founder.email == "test@example.com"

    async def test_project_default_values(self, db_session):
        # 기본값 테스트
        project = Project(title="Default Test", founder_id=1)
        db_session.add(project)
        await db_session.commit()

        assert project.description is None  # description이 선택적 필드인 경우
        assert project.is_deleted is False  # is_deleted 필드가 있는 경우

    async def test_project_cascade_delete(self, db_session):
        user = User(email="cascade@example.com", hashed_password="hashed_password")
        db_session.add(user)
        await db_session.commit()

        project = Project(title="Cascade Test", founder_id=user.id)
        db_session.add(project)
        await db_session.commit()

        # Delete the user
        await db_session.delete(user)
        await db_session.commit()

        # Check if the project is also deleted
        result = await db_session.execute(
            select(Project).where(Project.id == project.id)
        )
        assert result.scalar_one_or_none() is None

        # Additional check: try to fetch the user
        user_result = await db_session.execute(select(User).where(User.id == user.id))
        assert user_result.scalar_one_or_none() is None

    async def test_orphaned_project_delete(self, db_session):
        user = User(email="orphan@example.com", hashed_password="hashed_password")
        db_session.add(user)
        await db_session.commit()

        project = Project(title="Orphan Test", founder_id=user.id)
        db_session.add(project)
        await db_session.commit()

        # Refresh the user to load the projects relationship
        await db_session.refresh(user, ["projects"])

        # Remove the project from the user's projects
        user.projects = [p for p in user.projects if p.id != project.id]
        await db_session.commit()

        # Expire the user object to ensure we get fresh data
        await db_session.refresh(user)

        # Check if the project is deleted
        result = await db_session.execute(
            select(Project).where(Project.id == project.id)
        )
        assert result.scalar_one_or_none() is None

        # Ensure the user still exists
        user_result = await db_session.execute(select(User).where(User.id == user.id))
        assert user_result.scalar_one_or_none() is not None

    async def test_load_user_with_projects(self, db_session):
        user = User(
            email="user_with_projects@example.com", hashed_password="hashed_password"
        )
        db_session.add(user)
        await db_session.commit()

        project1 = Project(title="Project 1", founder_id=user.id)
        project2 = Project(title="Project 2", founder_id=user.id)
        db_session.add_all([project1, project2])
        await db_session.commit()

        # Load user with projects
        stmt = (
            select(User).options(selectinload(User.projects)).where(User.id == user.id)
        )
        result = await db_session.execute(stmt)
        loaded_user = result.scalar_one()

        assert len(loaded_user.projects) == 2
        assert all(isinstance(p, Project) for p in loaded_user.projects)
        assert set(p.title for p in loaded_user.projects) == {"Project 1", "Project 2"}
