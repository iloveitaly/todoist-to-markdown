"""Test todoist-to-markdown."""

import todoist_to_markdown


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(todoist_to_markdown.__name__, str)
