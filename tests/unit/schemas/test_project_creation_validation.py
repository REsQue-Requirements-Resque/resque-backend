import pytest
from pydantic import ValidationError
from app.schemas.project import ProjectCreate, ProjectUpdate


@pytest.mark.unit
@pytest.mark.schemas
class TestProjectSchemaValidation:
    @pytest.fixture
    def valid_data(self):
        return {
            "title": "Valid Project",
            "description": "This is a valid project description.",
        }

    def test_valid_project_creation(self, valid_data):
        project = ProjectCreate(**valid_data)
        assert project.title == valid_data["title"]
        assert project.description == valid_data["description"]

    def test_title_non_english(self, valid_data):
        data = valid_data.copy()
        data["title"] = "프로젝트"
        with pytest.raises(
            ValidationError,
            match="Project title must contain only English characters and numbers",
        ):
            ProjectCreate(**data)

    def test_title_too_short(self, valid_data):
        data = valid_data.copy()
        data["title"] = "ab"
        with pytest.raises(
            ValidationError, match="Project title must be between 3 and 100 characters"
        ):
            ProjectCreate(**data)

    def test_title_too_long(self, valid_data):
        data = valid_data.copy()
        data["title"] = "a" * 101
        with pytest.raises(
            ValidationError, match="Project title must be between 3 and 100 characters"
        ):
            ProjectCreate(**data)

    def test_description_too_long(self, valid_data):
        data = valid_data.copy()
        data["description"] = "a" * 1001
        with pytest.raises(
            ValidationError, match="Project description must not exceed 1000 characters"
        ):
            ProjectCreate(**data)

    def test_title_missing(self, valid_data):
        data = valid_data.copy()
        del data["title"]
        with pytest.raises(ValidationError, match="Field required"):
            ProjectCreate(**data)

    def test_description_optional(self, valid_data):
        data = valid_data.copy()
        del data["description"]
        project = ProjectCreate(**data)
        assert project.description is None

    def test_title_whitespace_stripped(self, valid_data):
        data = valid_data.copy()
        data["title"] = "  Whitespace  "
        project = ProjectCreate(**data)
        assert project.title == "Whitespace"

    def test_description_whitespace_stripped(self, valid_data):
        data = valid_data.copy()
        data["description"] = "  Description  "
        project = ProjectCreate(**data)
        assert project.description == "Description"

    def test_title_with_numbers(self, valid_data):
        data = valid_data.copy()
        data["title"] = "Project 123"
        project = ProjectCreate(**data)
        assert project.title == "Project 123"

    def test_empty_description(self, valid_data):
        data = valid_data.copy()
        data["description"] = ""
        project = ProjectCreate(**data)
        assert project.description == ""

    def test_description_only_whitespace(self, valid_data):
        data = valid_data.copy()
        data["description"] = "   "
        project = ProjectCreate(**data)
        assert project.description == ""

    def test_title_with_special_characters(self, valid_data):
        data = valid_data.copy()
        data["title"] = "Project@123"
        with pytest.raises(
            ValidationError,
            match="Project title must contain only English characters and numbers",
        ):
            ProjectCreate(**data)

    def test_title_minimum_length(self, valid_data):
        data = valid_data.copy()
        data["title"] = "abc"
        project = ProjectCreate(**data)
        assert project.title == "abc"

    def test_title_maximum_length(self, valid_data):
        data = valid_data.copy()
        data["title"] = "a" * 100
        project = ProjectCreate(**data)
        assert len(project.title) == 100

    def test_description_null(self, valid_data):
        data = valid_data.copy()
        data["description"] = None
        project = ProjectCreate(**data)
        assert project.description is None

    def test_title_leading_trailing_spaces(self, valid_data):
        data = valid_data.copy()
        data["title"] = "  Leading and trailing spaces  "
        project = ProjectCreate(**data)
        assert project.title == "Leading and trailing spaces"

    # ProjectUpdate 테스트
    def test_project_update_empty(self):
        with pytest.raises(ValidationError):
            ProjectUpdate()

    def test_project_update_partial(self):
        update = ProjectUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.description is None

    def test_project_update_full(self):
        update = ProjectUpdate(title="Updated Title", description="Updated Description")
        assert update.title == "Updated Title"
        assert update.description == "Updated Description"

    def test_project_update_invalid_title(self):
        with pytest.raises(
            ValidationError, match="Project title must be between 3 and 100 characters"
        ):
            ProjectUpdate(title="a")

    def test_project_update_invalid_description(self):
        with pytest.raises(
            ValidationError, match="Project description must not exceed 1000 characters"
        ):
            ProjectUpdate(description="a" * 1001)
