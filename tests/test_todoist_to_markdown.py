import os
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from todoist_to_markdown import extract_task_id, format_task_markdown, main


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


class TestMainCLI:
    def test_main_missing_api_key(self):
        runner = CliRunner()
        with patch.dict("os.environ", {}, clear=True):
            result = runner.invoke(main, ["https://app.todoist.com/app/task/test-123"])
            assert result.exit_code != 0
            assert "TODOIST_API_KEY environment variable required" in result.output

    @patch("todoist_to_markdown.TodoistAPI")
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

    @patch("todoist_to_markdown.TodoistAPI")
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
