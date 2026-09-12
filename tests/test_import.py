"""Test todoist-to-md."""

import todoist_to_md


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(todoist_to_md.__name__, str)


def test_version() -> None:
    """Test that the version is available."""
    assert isinstance(todoist_to_md.__version__, str)
