import pytest
from pydantic import ValidationError
from app.schemas.project import ProjectCreate


@pytest.mark.unit
@pytest.mark.req_14_project_creation
class TestProjectSchemaValidation:
    @classmethod
    def setup_class(cls):
        cls.valid_data = {
            "title": "Valid Project",
            "description": "This is a valid project description.",
            "founder_id": 1,
        }

    @classmethod
    def get_valid_data(cls):
        return cls.valid_data.copy()

    def test_valid_project_creation(self):
        project = ProjectCreate(**self.get_valid_data())
        assert project.title == self.valid_data["title"]
        assert project.description == self.valid_data["description"]
        assert project.founder_id == self.valid_data["founder_id"]

    def test_title_non_english(self):
        data = self.get_valid_data()
        data["title"] = "프로젝트"
        with pytest.raises(
            ValidationError, match="Project title must contain only English characters"
        ):
            ProjectCreate(**data)

    def test_title_too_short(self):
        data = self.get_valid_data()
        data["title"] = "ab"
        with pytest.raises(
            ValidationError, match="String should have at least 3 characters"
        ):
            ProjectCreate(**data)

    def test_title_too_long(self):
        data = self.get_valid_data()
        data["title"] = "a" * 101
        with pytest.raises(
            ValidationError, match="String should have at most 100 characters"
        ):
            ProjectCreate(**data)

    def test_description_too_long(self):
        data = self.get_valid_data()
        data["description"] = "a" * 1001
        with pytest.raises(
            ValidationError, match="String should have at most 1000 characters"
        ):
            ProjectCreate(**data)

    def test_title_missing(self):
        data = self.get_valid_data()
        del data["title"]
        with pytest.raises(ValidationError, match="field required"):
            ProjectCreate(**data)

    def test_description_optional(self):
        data = self.get_valid_data()
        del data["description"]
        project = ProjectCreate(**data)
        assert project.description is None

    def test_founder_id_must_be_positive(self):
        data = self.get_valid_data()
        data["founder_id"] = 0
        with pytest.raises(
            ValidationError, match="ensure this value is greater than 0"
        ):
            ProjectCreate(**data)

    def test_title_whitespace_stripped(self):
        data = self.get_valid_data()
        data["title"] = " Valid Project "
        project = ProjectCreate(**data)
        assert project.title == "Valid Project"

    def test_description_whitespace_preserved(self):
        data = self.get_valid_data()
        data["description"] = " This is a   valid description. "
        project = ProjectCreate(**data)
        assert project.description == " This is a   valid description. "
