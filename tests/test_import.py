"""Test todoist-to-md."""

import todoist_to_md


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(todoist_to_md.__name__, str)
