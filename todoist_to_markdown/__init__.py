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


def is_project_url(url: str) -> bool:
    """Check if URL is a project URL."""
    return "app.todoist.com" in url and "/project/" in url


def extract_project_id(url: str) -> str:
    """Extract project ID from Todoist project URL."""
    # Pattern: https://app.todoist.com/app/project/blah-9kqn6qrmHVJX6386
    # The project ID is the part after the last dash
    match = re.search(r"/project/([^/?#]+)", url)
    if not match:
        raise ValueError("invalid todoist project url format")

    full_slug = match.group(1)
    # Extract the project ID from the slug (part after the last dash)
    if "-" in full_slug:
        return full_slug.split("-")[-1]
    else:
        return full_slug


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
            instant = Instant.parse_iso(comment.posted_at)
            comment_date = instant.format_iso()[:10]
        except Exception as e:
            log.debug("date parsing error for comment: %s", str(e))
            comment_date = (
                str(comment.posted_at)[:10] if comment.posted_at else "unknown"
            )
        lines.append(f"## {comment_date}")
        lines.append("")
        lines.append(comment.content)
    return "\n".join(lines)


def format_project_markdown(project, tasks_with_comments: list, url: str) -> str:
    """Format multiple tasks from a project as markdown."""
    lines = [f"# {project.name}", ""]
    lines.append(f"Original: {url}")
    lines.append("")
    lines.append(f"Project ID: {project.id}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for task, comments in tasks_with_comments:
        lines.append(f"## {task.content}")
        lines.append("")
        if task.description:
            lines.append(task.description)
            lines.append("")

        # Add comments for this task if any exist
        if comments:
            for comment in comments:
                try:
                    instant = Instant.parse_iso(comment.posted_at)
                    comment_date = instant.format_iso()[:10]
                except Exception as e:
                    log.debug("date parsing error for comment: %s", str(e))
                    comment_date = (
                        str(comment.posted_at)[:10] if comment.posted_at else "unknown"
                    )
                lines.append(f"### {comment_date}")
                lines.append("")
                lines.append(comment.content)
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def process_project(api: TodoistAPI, project_id: str, url: str) -> str:
    """Fetch all tasks from a project and format as markdown."""
    log.info("extracting project %s", project_id)

    # Get project details
    project = api.get_project(project_id)

    # Get all tasks in the project (returns a paginated result)
    tasks_raw = list(api.get_tasks(project_id=project_id))

    # Normalize tasks (handle both list and single objects)
    tasks = []
    for t in tasks_raw:
        if isinstance(t, list):
            tasks.extend(t)
        else:
            tasks.append(t)

    # Fetch comments for each task
    tasks_with_comments = []
    for task in tasks:
        log.debug("fetching comments for task %s", task.id)
        comments_raw = list(api.get_comments(task_id=task.id))
        comments = []
        for c in comments_raw:
            if isinstance(c, list):
                comments.extend(c)
            else:
                comments.append(c)
        tasks_with_comments.append((task, comments))

    return format_project_markdown(project, tasks_with_comments, url)


def process_task(api: TodoistAPI, task_id: str, url: str) -> str:
    """Fetch a single task and format as markdown."""
    log.info("extracting task %s", task_id)

    task = api.get_task(task_id)
    comments_raw = list(api.get_comments(task_id=task_id))
    comments = []
    for c in comments_raw:
        if isinstance(c, list):
            comments.extend(c)
        else:
            comments.append(c)

    return format_task_markdown(task, comments, url)


@click.command()
@click.argument("url")
def main(url: str):
    """Convert Todoist task or project to markdown format."""
    api_token = os.environ.get("TODOIST_API_KEY")
    if not api_token:
        raise click.ClickException("TODOIST_API_KEY environment variable required")

    try:
        api = TodoistAPI(api_token)

        # Determine if URL is for a project or a task
        if is_project_url(url):
            project_id = extract_project_id(url)
            markdown = process_project(api, project_id, url)
        else:
            task_id = extract_task_id(url)
            markdown = process_task(api, task_id, url)

        click.echo(markdown)

    except Exception as e:
        log.error("failed to process: %s", str(e))
        raise click.ClickException(f"error: {e}")


if __name__ == "__main__":
    main()
