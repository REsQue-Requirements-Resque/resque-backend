import pytest
from sqlalchemy.exc import IntegrityError
from app.models.project import Project
from app.models.user import User  # User 모델이 필요할 경우
from datetime import datetime


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
        assert project.founder == user
        assert project in user.projects

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

        # Check if the project is also deleted (if cascade delete is set up)
        assert await db_session.get(Project, project.id) is None
