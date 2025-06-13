# Todoist to Markdown

Convert Todoist tasks to markdown format.

## Usage

1. Set your Todoist API token:

```bash
export TODOIST_API_TOKEN="your_api_token_here"
```

1. Run the tool with a Todoist task URL:

```bash
todoist-to-markdown https://app.todoist.com/app/task/family-critique-6WHj3H6XmQ6F5HJJ
```

## Output Format

The tool outputs tasks and comments in this markdown template format:

```markdown
# TASK_NAME

Project: PROJECT_NAME

TASK_DESCRIPTION

## DATE_OF_FIRST_COMMENT

COMMENT_DESCRIPTION

## DATE_OF_NEXT_COMMENT

COMMENT_DESCRIPTION
```