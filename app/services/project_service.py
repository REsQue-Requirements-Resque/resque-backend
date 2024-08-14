from app.repositories.project_repository import ProjectRepository
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    def create_project(self, project_data: ProjectCreate) -> Project:
        return self.project_repo.create(Project(**project_data.model_dump()))

    def get_project(self, project_id: int) -> Project:
        return self.project_repo.get(project_id)

    def update_project(self, project_id: int, project_data: ProjectUpdate) -> Project:
        return self.project_repo.update(project_id, project_data.model_dump())

    def delete_project(self, project_id: int) -> bool:
        return self.project_repo.delete(project_id)

    def list_projects(self) -> list[Project]:
        return self.project_repo.list()
