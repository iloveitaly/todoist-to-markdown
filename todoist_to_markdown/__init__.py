import logging
import os
import re
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from todoist_api_python.api import TodoistAPI
from whenever import Instant

# Set up rich logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

log = logging.getLogger(__name__)
console = Console()


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
            try:
                instant = Instant.parse_common_iso(comment.posted_at)
                comment_date = instant.format_common_iso()[:16].replace("T", " ")
            except Exception as e:
                log.debug("date parsing error for comment: %s", str(e))
                comment_date = str(comment.posted_at) if comment.posted_at else "unknown date"

            lines.append(f"### {comment_date}")
            lines.append("")
            lines.append(comment.content)

    return "\n".join(lines)


@click.command()
@click.argument("url")
@click.option("--output", "-o", type=click.Path(), help="Output markdown to a file")
def main(url: str, output: Optional[str] = None):
    """Convert Todoist task to markdown format."""
    api_token = os.environ.get("TODOIST_API_KEY")
    if not api_token:
        raise click.ClickException("TODOIST_API_KEY environment variable required")

    try:
        task_id = extract_task_id(url)
        log.info(f"Fetching task {task_id}...")

        api = TodoistAPI(api_token)

        # Fetch task details
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

        # Fetch comments
        log.info("Fetching comments...")
        comments_raw = list(api.get_comments(task_id=task_id))
        comments = []
        for c in comments_raw:
            if isinstance(c, list):
                comments.extend(c)
            else:
                comments.append(c)

        markdown = format_task_markdown(
            task,
            comments,
            url,
            project_name=project_name,
            section_name=section_name,
        )

        if output:
            with open(output, "w") as f:
                f.write(markdown)
            console.print(f"[green]Successfully saved markdown to {output}[/green]")
        else:
            click.echo(markdown)

    except Exception as e:
        log.error(f"Failed to process task: {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
