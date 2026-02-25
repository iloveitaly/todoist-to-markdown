[![Release Notes](https://img.shields.io/github/release/iloveitaly/todoist-to-markdown)](https://github.com/iloveitaly/todoist-to-markdown/releases)
[![Downloads](https://static.pepy.tech/badge/todoist-to-markdown/month)](https://pepy.tech/project/todoist-to-markdown)
![GitHub CI Status](https://github.com/iloveitaly/todoist-to-markdown/actions/workflows/build_and_publish.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Todoist to Markdown

Convert a Todoist task (and its comments) into a clean, readable Markdown format. Perfect for archiving tasks or migrating notes.

This tool was completely AI-generated. I didn't write any code, although I did use [some fancy rules](https://github.com/iloveitaly/llm-ide-prompts) and a [package starter template](https://github.com/iloveitaly/python-package-template).

## Installation

```bash
uv tool install todoist-to-markdown
```

## Usage

1. **Set your Todoist API token:**

   You can find your API token in the [Todoist Integrations settings](https://todoist.com/app/settings/integrations).

   ```bash
   export TODOIST_API_KEY="your_api_token_here"
   ```

2. **Run the tool with a Todoist task URL:**

   ```bash
   todoist-to-markdown https://app.todoist.com/app/task/family-notes-6WHj3H6XmQ6F5HJJ
   ```

3. **Save output to a file:**

   ```bash
   todoist-to-markdown https://app.todoist.com/app/task/family-notes-6WHj3H6XmQ6F5HJJ --output task.md
   ```

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

---

*This project was created from [iloveitaly/python-package-template](https://github.com/iloveitaly/python-package-template)*
