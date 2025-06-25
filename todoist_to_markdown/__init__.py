import logging
import os
import re

import click
from todoist_api_python.api import TodoistAPI
from whenever import Instant

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
)

log = logging.getLogger(__name__)


def extract_task_id(url: str) -> str:
    """Extract task ID from Todoist URL."""
    # Pattern: https://app.todoist.com/app/task/family-critique-6WHj3H6XmQ6F5HJJ
    # The task ID is the part after the last dash
    match = re.search(r"/task/([^/?#]+)", url)
    if not match:
        raise ValueError("invalid todoist task url format")

    full_slug = match.group(1)
    # Extract the task ID from the slug (part after the last dash)
    if "-" in full_slug:
        return full_slug.split("-")[-1]
    else:
        return full_slug


def format_task_markdown(task, comments: list, url: str) -> str:
    lines = [f"# {task.content}", ""]
    lines.append(f"Original: {url}")
    lines.append("")
    if task.project_id:
        lines.append(f"Project: {task.project_id}")
    if task.description:
        if task.project_id:
            lines.append("")
        lines.append(task.description)
    for comment in comments:
        lines.append("")
        try:
            instant = Instant.parse_common_iso(comment.posted_at)
            comment_date = instant.format_common_iso()[:10]
        except Exception as e:
            log.debug("date parsing error for comment: %s", str(e))
            comment_date = str(comment.posted_at)[:10] if comment.posted_at else "unknown"
        lines.append(f"## {comment_date}")
        lines.append("")
        lines.append(comment.content)
    return "\n".join(lines)


@click.command()
@click.argument("url")
def main(url: str):
    """Convert Todoist task to markdown format."""
    api_token = os.environ.get("TODOIST_API_KEY")
    if not api_token:
        raise click.ClickException("TODOIST_API_KEY environment variable required")

    try:
        task_id = extract_task_id(url)
        log.info("extracting task %s", task_id)

        api = TodoistAPI(api_token)

        task = api.get_task(task_id)
        comments_raw = list(api.get_comments(task_id=task_id))
        comments = []
        for c in comments_raw:
            if isinstance(c, list):
                comments.extend(c)
            else:
                comments.append(c)
        markdown = format_task_markdown(task, comments, url)
        click.echo(markdown)

    except Exception as e:
        log.error("failed to process task: %s", str(e))
        raise click.ClickException(f"error: {e}")


if __name__ == "__main__":
    main()
