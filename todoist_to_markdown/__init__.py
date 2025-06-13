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
    match = re.search(r'/task/([^/?]+)', url)
    if not match:
        raise ValueError("invalid todoist task url format")
    return match.group(1)


def format_task_markdown(task, comments: list) -> str:
    """Format task and comments into markdown template."""
    lines = ["```"]
    lines.append(f"# {task.content}")
    lines.append("")
    
    if task.project_id:
        lines.append(f"Project: {task.project_id}")
    
    if task.description:
        lines.append("")
        lines.append(task.description)
    
    for comment in comments:
        lines.append("")
        comment_date = Instant.parse_rfc3339(comment.posted_at).format_common_iso()[:10]
        lines.append(f"## {comment_date}")
        lines.append("")
        lines.append(comment.content)
    
    lines.append("```")
    return "\n".join(lines)


@click.command()
@click.argument('url')
def main(url: str):
    """Convert Todoist task to markdown format."""
    api_token = os.environ.get("TODOIST_API_TOKEN")
    if not api_token:
        raise click.ClickException("TODOIST_API_TOKEN environment variable required")
    
    try:
        task_id = extract_task_id(url)
        log.info("extracting task %s", task_id)
        
        api = TodoistAPI(api_token)
        
        task = api.get_task(task_id)
        comments = api.get_comments(task_id=task_id)
        
        markdown = format_task_markdown(task, comments)
        click.echo(markdown)
        
    except Exception as e:
        log.error("failed to process task: %s", str(e))
        raise click.ClickException(f"error: {e}")


if __name__ == "__main__":
    main()
