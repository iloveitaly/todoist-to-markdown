import logging
import os
import re
from typing import Optional

import click
from todoist_api_python.api import TodoistAPI
from whenever import Instant

# Set up standard logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

log = logging.getLogger(__name__)


def is_project_url(url: str) -> bool:
    """Check if URL is a project URL."""
    return "app.todoist.com" in url and "/project/" in url


def _extract_slug_id(path_segment: str) -> str:
    """Extract the ID from a URL path slug (part after the last dash)."""
    if "-" in path_segment:
        return path_segment.split("-")[-1]
    return path_segment


def extract_project_id(url: str) -> str:
    """Extract project ID from Todoist project URL.

    Supports:
    - https://app.todoist.com/app/project/slug-ID
    - https://app.todoist.com/app/project/ID
    - https://todoist.com/showProject?id=ID
    """
    match = re.search(r"/project/([^/?#]+)", url)
    if match:
        return _extract_slug_id(match.group(1))

    query_match = re.search(r"id=(\d+)", url)
    if query_match:
        return query_match.group(1)

    raise ValueError(f"Invalid Todoist project URL format: {url}")


def extract_task_id(url: str) -> str:
    """Extract task ID from Todoist URL.

    Supports:
    - https://app.todoist.com/app/task/slug-ID
    - https://todoist.com/showTask?id=ID
    - https://todoist.com/app/task/ID
    """
    match = re.search(r"/task/([^/?#]+)", url)
    if match:
        return _extract_slug_id(match.group(1))

    query_match = re.search(r"id=(\d+)", url)
    if query_match:
        return query_match.group(1)

    raise ValueError(f"Invalid Todoist task URL format: {url}")


def _format_comment_date(posted_at: str) -> str:
    """Parse and format a comment's posted_at timestamp to 'YYYY-MM-DD HH:MM'."""
    try:
        instant = Instant.parse_iso(posted_at)
        return instant.format_iso()[:16].replace("T", " ")
    except Exception as e:
        log.debug("date parsing error for comment: %s", str(e))
        return str(posted_at) if posted_at else "unknown date"


def format_task_markdown(
    task,
    comments: list,
    url: str,
    project_name: Optional[str] = None,
    section_name: Optional[str] = None,
) -> str:
    """Format task and comments into a markdown string."""
    lines = [f"# {task.content}", ""]
    lines.append(f"**Original:** {url}")

    metadata = []
    if project_name:
        metadata.append(f"**Project:** {project_name}")
    elif task.project_id:
        metadata.append(f"**Project ID:** {task.project_id}")

    if section_name:
        metadata.append(f"**Section:** {section_name}")

    if metadata:
        lines.append("")
        lines.extend(metadata)

    if task.description:
        lines.append("")
        lines.append("## Description")
        lines.append("")
        lines.append(task.description)

    if comments:
        lines.append("")
        lines.append("## Comments")
        for comment in comments:
            lines.append("")
            lines.append(f"### {_format_comment_date(comment.posted_at)}")
            lines.append("")
            lines.append(comment.content)

    return "\n".join(lines)


def format_project_markdown(project, tasks_with_comments: list, url: str) -> str:
    """Format multiple tasks from a project as markdown."""
    lines = [f"# {project.name}", ""]
    lines.append(f"**Original:** {url}")
    lines.append("")
    lines.append(f"**Project ID:** {project.id}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for task, comments in tasks_with_comments:
        lines.append(f"## {task.content}")
        lines.append("")
        if task.description:
            lines.append(task.description)
            lines.append("")

        if comments:
            for comment in comments:
                lines.append(f"### {_format_comment_date(comment.posted_at)}")
                lines.append("")
                lines.append(comment.content)
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _fetch_comments(api: TodoistAPI, task_id: str) -> list:
    """Fetch and normalize comments for a task."""
    comments_raw = list(api.get_comments(task_id=task_id))
    comments = []
    for c in comments_raw:
        if isinstance(c, list):
            comments.extend(c)
        else:
            comments.append(c)
    return comments


def _process_task(api: TodoistAPI, task_id: str, url: str) -> str:
    """Fetch a single task and format as markdown."""
    log.info(f"Fetching task {task_id}...")

    task = api.get_task(task_id)

    # Fetch project name
    project_name = None
    if task.project_id:
        try:
            project = api.get_project(task.project_id)
            project_name = project.name
        except Exception:
            log.warning(f"Could not fetch project name for ID {task.project_id}")

    # Fetch section name
    section_name = None
    if task.section_id:
        try:
            section = api.get_section(task.section_id)
            section_name = section.name
        except Exception:
            log.warning(f"Could not fetch section name for ID {task.section_id}")

    comments = _fetch_comments(api, task_id)

    return format_task_markdown(
        task,
        comments,
        url,
        project_name=project_name,
        section_name=section_name,
    )


def _process_project(api: TodoistAPI, project_id: str, url: str) -> str:
    """Fetch all tasks from a project and format as markdown."""
    log.info(f"Fetching project {project_id}...")

    project = api.get_project(project_id)

    tasks_raw = list(api.get_tasks(project_id=project_id))
    tasks = []
    for t in tasks_raw:
        if isinstance(t, list):
            tasks.extend(t)
        else:
            tasks.append(t)

    tasks_with_comments = []
    for task in tasks:
        comments = _fetch_comments(api, task.id)
        tasks_with_comments.append((task, comments))

    return format_project_markdown(project, tasks_with_comments, url)


@click.command()
@click.argument("url")
@click.option("--output", "-o", type=click.Path(), help="Output markdown to a file")
def main(url: str, output: Optional[str] = None):
    """Convert Todoist task or project to markdown format."""
    api_token = os.environ.get("TODOIST_API_KEY")
    if not api_token:
        raise click.ClickException("TODOIST_API_KEY environment variable required")

    try:
        api = TodoistAPI(api_token)

        if is_project_url(url):
            project_id = extract_project_id(url)
            markdown = _process_project(api, project_id, url)
        else:
            task_id = extract_task_id(url)
            markdown = _process_task(api, task_id, url)

        if output:
            with open(output, "w") as f:
                f.write(markdown)
            click.echo(f"Successfully saved markdown to {output}")
        else:
            click.echo(markdown)

    except Exception as e:
        log.error(f"Failed to process: {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
