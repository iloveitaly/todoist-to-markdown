# Todoist to Markdown

Convert a Todoist task to markdown format.

This tool was completely AI generated. I didn't write any code although I did use [some fancy rules](https://github.com/iloveitaly/llm-ide-prompts)
and a [package starter template](https://github.com/iloveitaly/python-package-template).

## Usage

1. Set your Todoist API token:

```bash
export TODOIST_API_KEY="your_api_token_here"
```

1. Run the tool with a Todoist task URL:

```bash
todoist-to-markdown https://app.todoist.com/app/task/family-notes-6WHj3H6XmQ6F5HJJ
```

The tool will output the task and its comments in markdown format.

## Example Output

```markdown
# Family Notes

Project: Personal

Review the family photos and provide feedback on composition and lighting.

## 2025-06-13

Initial thoughts: The composition looks good but we need better lighting.

## 2025-06-14

Added some suggestions for the next photo session.
```
