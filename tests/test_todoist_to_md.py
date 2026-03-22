import os
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from todoist_to_md import (
    extract_project_id,
    extract_task_id,
    format_project_markdown,
    format_task_markdown,
    is_project_url,
    main,
)


class TestExtractTaskId:
    def test_extract_task_id_valid_url(self):
        url = "https://app.todoist.com/app/task/family-critique-6WHj3H6XmQ6F5HJJ"
        result = extract_task_id(url)
        assert result == "6WHj3H6XmQ6F5HJJ"

    def test_extract_task_id_with_query_params(self):
        url = "https://app.todoist.com/app/task/family-critique-6WHj3H6XmQ6F5HJJ?param=value"
        result = extract_task_id(url)
        assert result == "6WHj3H6XmQ6F5HJJ"

    def test_extract_task_id_with_fragment(self):
        url = (
            "https://app.todoist.com/app/task/family-critique-6WHj3H6XmQ6F5HJJ#section"
        )
        result = extract_task_id(url)
        assert result == "6WHj3H6XmQ6F5HJJ"

    def test_extract_task_id_invalid_url(self):
        with pytest.raises(ValueError, match="Invalid Todoist task URL format"):
            extract_task_id("https://example.com/not-a-task")

    def test_extract_task_id_no_dashes(self):
        url = "https://app.todoist.com/app/task/6WHj3H6XmQ6F5HJJ"
        result = extract_task_id(url)
        assert result == "6WHj3H6XmQ6F5HJJ"

    def test_extract_task_id_query_param(self):
        url = "https://todoist.com/showTask?id=123456789"
        result = extract_task_id(url)
        assert result == "123456789"


class TestIsProjectUrl:
    def test_is_project_url_true(self):
        assert is_project_url(
            "https://app.todoist.com/app/project/blah-9kqn6qrmHVJX6386"
        )

    def test_is_project_url_false_task(self):
        assert not is_project_url("https://app.todoist.com/app/task/test-123")

    def test_is_project_url_false_other(self):
        assert not is_project_url("https://example.com/project/test")


class TestExtractProjectId:
    def test_extract_project_id_valid_url(self):
        url = "https://app.todoist.com/app/project/blah-9kqn6qrmHVJX6386"
        result = extract_project_id(url)
        assert result == "9kqn6qrmHVJX6386"

    def test_extract_project_id_with_query_params(self):
        url = "https://app.todoist.com/app/project/blah-9kqn6qrmHVJX6386?param=value"
        result = extract_project_id(url)
        assert result == "9kqn6qrmHVJX6386"

    def test_extract_project_id_with_fragment(self):
        url = "https://app.todoist.com/app/project/blah-9kqn6qrmHVJX6386#section"
        result = extract_project_id(url)
        assert result == "9kqn6qrmHVJX6386"

    def test_extract_project_id_invalid_url(self):
        with pytest.raises(ValueError, match="Invalid Todoist project URL format"):
            extract_project_id("https://example.com/not-a-project")

    def test_extract_project_id_no_dashes(self):
        url = "https://app.todoist.com/app/project/9kqn6qrmHVJX6386"
        result = extract_project_id(url)
        assert result == "9kqn6qrmHVJX6386"


class TestFormatTaskMarkdown:
    def test_format_task_basic(self):
        task = Mock()
        task.content = "Test Task"
        task.project_id = "project123"
        task.section_id = None
        task.description = "Task description"

        comments = []
        url = "https://app.todoist.com/app/task/test-123"
        result = format_task_markdown(task, comments, url, project_name="My Project")

        assert "# Test Task" in result
        assert "**Original:** https://app.todoist.com/app/task/test-123" in result
        assert "**Project:** My Project" in result
        assert "## Description" in result
        assert "Task description" in result

    def test_format_task_with_comments(self):
        task = Mock()
        task.content = "Test Task"
        task.project_id = "project123"
        task.section_id = "section456"
        task.description = "Task description"

        comment1 = Mock()
        comment1.posted_at = "2025-06-13T10:30:00Z"
        comment1.content = "First comment"

        comments = [comment1]
        url = "https://app.todoist.com/app/task/test-123"
        result = format_task_markdown(
            task,
            comments,
            url,
            project_name="My Project",
            section_name="My Section",
        )

        assert "**Project:** My Project" in result
        assert "**Section:** My Section" in result
        assert "## Comments" in result
        assert "### 2025-06-13 10:30" in result
        assert "First comment" in result


class TestFormatProjectMarkdown:
    def test_format_project_basic(self):
        project = Mock()
        project.name = "Test Project"
        project.id = "project123"

        task1 = Mock()
        task1.content = "Task 1"
        task1.description = "Description 1"

        task2 = Mock()
        task2.content = "Task 2"
        task2.description = None

        tasks_with_comments = [(task1, []), (task2, [])]
        url = "https://app.todoist.com/app/project/test-project123"
        result = format_project_markdown(project, tasks_with_comments, url)

        assert "# Test Project" in result
        assert (
            "**Original:** https://app.todoist.com/app/project/test-project123"
            in result
        )
        assert "**Project ID:** project123" in result
        assert "## Task 1" in result
        assert "Description 1" in result
        assert "## Task 2" in result
        assert "---" in result

    def test_format_project_with_comments(self):
        project = Mock()
        project.name = "Test Project"
        project.id = "project123"

        task = Mock()
        task.content = "Task 1"
        task.description = "Task description"

        comment1 = Mock()
        comment1.posted_at = "2025-06-13T10:30:00Z"
        comment1.content = "First comment"

        comment2 = Mock()
        comment2.posted_at = "2025-06-14T15:45:00Z"
        comment2.content = "Second comment"

        tasks_with_comments = [(task, [comment1, comment2])]
        url = "https://app.todoist.com/app/project/test-project123"
        result = format_project_markdown(project, tasks_with_comments, url)

        assert "# Test Project" in result
        assert "## Task 1" in result
        assert "Task description" in result
        assert "### 2025-06-13 10:30" in result
        assert "First comment" in result
        assert "### 2025-06-14 15:45" in result
        assert "Second comment" in result


class TestMainCLI:
    def test_main_missing_api_key(self):
        runner = CliRunner()
        with patch.dict("os.environ", {}, clear=True):
            result = runner.invoke(main, ["https://app.todoist.com/app/task/test-123"])
            assert result.exit_code != 0
            assert "TODOIST_API_KEY environment variable required" in result.output

    @patch("todoist_to_md.TodoistAPI")
    def test_main_success(self, mock_api_class):
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        mock_task = Mock()
        mock_task.content = "Test Task"
        mock_task.project_id = "project123"
        mock_task.section_id = "section456"
        mock_task.description = "Test description"

        mock_project = Mock()
        mock_project.name = "Real Project Name"

        mock_section = Mock()
        mock_section.name = "Real Section Name"

        mock_comment = Mock()
        mock_comment.posted_at = "2025-06-13T10:30:00Z"
        mock_comment.content = "Test comment"

        mock_api.get_task.return_value = mock_task
        mock_api.get_project.return_value = mock_project
        mock_api.get_section.return_value = mock_section
        mock_api.get_comments.return_value = [mock_comment]

        runner = CliRunner()
        url = "https://app.todoist.com/app/task/test-123"
        with patch.dict("os.environ", {"TODOIST_API_KEY": "test-token"}):
            result = runner.invoke(main, [url])

        assert result.exit_code == 0
        assert "# Test Task" in result.output
        assert "**Project:** Real Project Name" in result.output
        assert "**Section:** Real Section Name" in result.output
        assert "Test comment" in result.output

    @patch("todoist_to_md.TodoistAPI")
    def test_main_output_file(self, mock_api_class, tmp_path):
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_api.get_task.return_value = Mock(
            content="Test", project_id=None, section_id=None, description=None
        )
        mock_api.get_comments.return_value = []

        output_file = tmp_path / "test.md"
        runner = CliRunner()
        url = "https://app.todoist.com/app/task/test-123"
        with patch.dict("os.environ", {"TODOIST_API_KEY": "test-token"}):
            result = runner.invoke(main, [url, "--output", str(output_file)])

        assert result.exit_code == 0
        assert os.path.exists(output_file)
        with open(output_file) as f:
            content = f.read()
            assert "# Test" in content

    @patch("todoist_to_md.TodoistAPI")
    def test_main_project_success(self, mock_api_class):
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.id = "project123"

        mock_task1 = Mock()
        mock_task1.id = "task1"
        mock_task1.content = "Task 1"
        mock_task1.description = "Description 1"

        mock_task2 = Mock()
        mock_task2.id = "task2"
        mock_task2.content = "Task 2"
        mock_task2.description = None

        mock_comment = Mock()
        mock_comment.posted_at = "2025-06-13T10:30:00Z"
        mock_comment.content = "Test comment"

        mock_api.get_project.return_value = mock_project
        mock_api.get_tasks.return_value = [mock_task1, mock_task2]
        mock_api.get_comments.side_effect = [[mock_comment], []]

        runner = CliRunner()
        url = "https://app.todoist.com/app/project/test-project123"
        with patch.dict("os.environ", {"TODOIST_API_KEY": "test-token"}):
            result = runner.invoke(main, [url])

        assert result.exit_code == 0
        assert "# Test Project" in result.output
        assert (
            "**Original:** https://app.todoist.com/app/project/test-project123"
            in result.output
        )
        assert "**Project ID:** project123" in result.output
        assert "## Task 1" in result.output
        assert "Description 1" in result.output
        assert "## Task 2" in result.output
        assert "### 2025-06-13 10:30" in result.output
        assert "Test comment" in result.output

    @patch("todoist_to_md.TodoistAPI")
    def test_main_project_api_error(self, mock_api_class):
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_api.get_project.side_effect = Exception("API Error")

        runner = CliRunner()
        with patch.dict("os.environ", {"TODOIST_API_KEY": "test-token"}):
            result = runner.invoke(
                main, ["https://app.todoist.com/app/project/test-123"]
            )

        assert result.exit_code != 0

    def test_main_invalid_url(self):
        runner = CliRunner()
        with patch.dict("os.environ", {"TODOIST_API_KEY": "test-token"}):
            result = runner.invoke(main, ["https://example.com/invalid"])

        assert result.exit_code != 0
