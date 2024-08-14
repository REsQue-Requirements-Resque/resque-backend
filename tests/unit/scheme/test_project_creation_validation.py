import pytest
from pydantic import ValidationError
from app.schemas.project import ProjectCreate  # 실제 경로에 맞게 수정해야 합니다


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
        data["title"] = "프로젝트123"
        with pytest.raises(
            ValidationError,
            match="Project title must contain only English characters and numbers",
        ):
            ProjectCreate(**data)

    def test_title_too_short(self):
        data = self.get_valid_data()
        data["title"] = "ab"
        with pytest.raises(
            ValidationError, match="Project title must be between 3 and 100 characters"
        ):
            ProjectCreate(**data)

    def test_title_too_long(self):
        data = self.get_valid_data()
        data["title"] = "a" * 101
        with pytest.raises(
            ValidationError, match="Project title must be between 3 and 100 characters"
        ):
            ProjectCreate(**data)

    def test_description_too_long(self):
        data = self.get_valid_data()
        data["description"] = "a" * 1001
        with pytest.raises(
            ValidationError, match="Project description must not exceed 1000 characters"
        ):
            ProjectCreate(**data)

    def test_title_missing(self):
        data = self.get_valid_data()
        del data["title"]
        with pytest.raises(ValidationError, match="Field required"):
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
            ValidationError, match="Founder ID must be a positive integer"
        ):
            ProjectCreate(**data)

    def test_title_whitespace_stripped(self):
        data = self.get_valid_data()
        data["title"] = " Valid Project "
        project = ProjectCreate(**data)
        assert project.title == "Valid Project"

    def test_description_whitespace_stripped(self):
        data = self.get_valid_data()
        data["description"] = " This is a   valid description. "
        project = ProjectCreate(**data)
        assert project.description == "This is a   valid description."

    def test_title_with_numbers(self):
        data = self.get_valid_data()
        data["title"] = "Project 123"
        project = ProjectCreate(**data)
        assert project.title == "Project 123"

    def test_empty_description(self):
        data = self.get_valid_data()
        data["description"] = ""
        project = ProjectCreate(**data)
        assert project.description == ""

    def test_description_only_whitespace(self):
        data = self.get_valid_data()
        data["description"] = "   "
        project = ProjectCreate(**data)
        assert project.description == ""

    def test_founder_id_string(self):
        data = self.get_valid_data()
        data["founder_id"] = "1"
        with pytest.raises(ValidationError, match="Input should be a valid integer"):
            ProjectCreate(**data)

    def test_founder_id_float(self):
        data = self.get_valid_data()
        data["founder_id"] = 1.5
        with pytest.raises(ValidationError, match="Input should be a valid integer"):
            ProjectCreate(**data)

    def test_founder_id_zero(self):
        data = self.get_valid_data()
        data["founder_id"] = 0
        with pytest.raises(
            ValidationError, match="Founder ID must be a positive integer"
        ):
            ProjectCreate(**data)

    def test_founder_id_negative(self):
        data = self.get_valid_data()
        data["founder_id"] = -1
        with pytest.raises(
            ValidationError, match="Founder ID must be a positive integer"
        ):
            ProjectCreate(**data)
