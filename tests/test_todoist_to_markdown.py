from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from todoist_to_markdown import (
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
        with pytest.raises(ValueError, match="invalid todoist task url format"):
            extract_task_id("https://example.com/not-a-task")

    def test_extract_task_id_no_task_id(self):
        with pytest.raises(ValueError, match="invalid todoist task url format"):
            extract_task_id("https://app.todoist.com/app/")

    def test_extract_task_id_no_dashes(self):
        url = "https://app.todoist.com/app/task/6WHj3H6XmQ6F5HJJ"
        result = extract_task_id(url)
        assert result == "6WHj3H6XmQ6F5HJJ"


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
        with pytest.raises(ValueError, match="invalid todoist project url format"):
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
        task.description = "Task description"

        comments = []
        url = "https://app.todoist.com/app/task/test-123"
        result = format_task_markdown(task, comments, url)

        expected = """# Test Task

Original: https://app.todoist.com/app/task/test-123

Project: project123

Task description"""
        assert result == expected

    def test_format_task_with_comments(self):
        task = Mock()
        task.content = "Test Task"
        task.project_id = "project123"
        task.description = "Task description"

        comment1 = Mock()
        comment1.posted_at = "2025-06-13T10:30:00Z"
        comment1.content = "First comment"

        comment2 = Mock()
        comment2.posted_at = "2025-06-14T15:45:00Z"
        comment2.content = "Second comment"

        comments = [comment1, comment2]
        url = "https://app.todoist.com/app/task/test-123"
        result = format_task_markdown(task, comments, url)

        expected = """# Test Task

Original: https://app.todoist.com/app/task/test-123

Project: project123

Task description

## 2025-06-13

First comment

## 2025-06-14

Second comment"""
        assert result == expected

    def test_format_task_no_description(self):
        task = Mock()
        task.content = "Test Task"
        task.project_id = "project123"
        task.description = None

        comments = []
        url = "https://app.todoist.com/app/task/test-123"
        result = format_task_markdown(task, comments, url)

        expected = """# Test Task

Original: https://app.todoist.com/app/task/test-123

Project: project123"""
        assert result == expected

    def test_format_task_no_project(self):
        task = Mock()
        task.content = "Test Task"
        task.project_id = None
        task.description = "Task description"

        comments = []
        url = "https://app.todoist.com/app/task/test-123"
        result = format_task_markdown(task, comments, url)

        expected = """# Test Task

Original: https://app.todoist.com/app/task/test-123

Task description"""
        assert result == expected


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

        expected = """# Test Project

Original: https://app.todoist.com/app/project/test-project123

Project ID: project123

---

## Task 1

Description 1

---

## Task 2

---
"""
        assert result == expected

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

        expected = """# Test Project

Original: https://app.todoist.com/app/project/test-project123

Project ID: project123

---

## Task 1

Task description

### 2025-06-13

First comment

### 2025-06-14

Second comment

---
"""
        assert result == expected


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
        mock_task.description = "Test description"

        mock_comment = Mock()
        mock_comment.posted_at = "2025-06-13T10:30:00Z"
        mock_comment.content = "Test comment"

        mock_api.get_task.return_value = mock_task
        mock_api.get_comments.return_value = [mock_comment]

        runner = CliRunner()
        url = "https://app.todoist.com/app/task/test-123"
        with patch.dict("os.environ", {"TODOIST_API_KEY": "test-token"}):
            result = runner.invoke(main, [url])

        assert result.exit_code == 0
        assert "# Test Task" in result.output
        assert "Original: https://app.todoist.com/app/task/test-123" in result.output
        assert "Project: project123" in result.output
        assert "Test description" in result.output
        assert "## 2025-06-13" in result.output
        assert "Test comment" in result.output

    @patch("todoist_to_markdown.TodoistAPI")
    def test_main_api_error(self, mock_api_class):
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_api.get_task.side_effect = Exception("API Error")

        runner = CliRunner()
        with patch.dict("os.environ", {"TODOIST_API_KEY": "test-token"}):
            result = runner.invoke(main, ["https://app.todoist.com/app/task/test-123"])

        assert result.exit_code != 0
        assert "error: API Error" in result.output

    def test_main_invalid_url(self):
        runner = CliRunner()
        with patch.dict("os.environ", {"TODOIST_API_KEY": "test-token"}):
            result = runner.invoke(main, ["https://example.com/invalid"])

        assert result.exit_code != 0
        assert "invalid todoist task url format" in result.output

    @patch("todoist_to_markdown.TodoistAPI")
    def test_main_project_success(self, mock_api_class):
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # Mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.id = "project123"

        # Mock tasks
        mock_task1 = Mock()
        mock_task1.id = "task1"
        mock_task1.content = "Task 1"
        mock_task1.description = "Description 1"

        mock_task2 = Mock()
        mock_task2.id = "task2"
        mock_task2.content = "Task 2"
        mock_task2.description = None

        # Mock comments
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
            "Original: https://app.todoist.com/app/project/test-project123"
            in result.output
        )
        assert "Project ID: project123" in result.output
        assert "## Task 1" in result.output
        assert "Description 1" in result.output
        assert "## Task 2" in result.output
        assert "### 2025-06-13" in result.output
        assert "Test comment" in result.output

    @patch("todoist_to_markdown.TodoistAPI")
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
        assert "error: API Error" in result.output
