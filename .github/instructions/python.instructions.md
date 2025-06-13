---
applyTo: "**/*.py"
---


When writing Python:

* Assume the latest python, version 3.13.
* Prefer Pathlib methods (including read and write methods, like `read_text`) over `os.path`, `open`, `write`, etc.
* Prefer modern typing: `list[str]` over `List[str]`, `dict[str, int]` over `Dict[str, int]`, etc.
* Use Pydantic models over dataclass or a typed dict.
* Use SQLAlchemy for generating any SQL queries.
* Use `click` for command line argument parsing.
* Use `log.info("the message", the_variable=the_variable)` instead of `log.info("The message: %s", the_variable)` or `print` for logging. This object can be found at `from app import log`.
  * Log messages should be lowercase with no leading or trailing whitespace.
  * No variable interpolation in log messages.

### Date & DateTime

* Use the `whenever` library for datetime + time instead of the stdlib date library. `Instant.now().format_common_iso()`

### Database & ORM

When accessing database records:

* SQLModel (wrapping SQLAlchemy) is used
* Do not manage database sessions, these are managed by a custom tool
  * Use `TheModel(...).save()` to persist a record
  * Use `TheModel.where(...).order_by(...)` to query records. `.where()` returns a SQLAlchemy select object that you can further customize the query.

When writing database models:

* Don't use `Field(...)` unless required. For instance, use `= None` instead of `= Field(default=None)`.
* Add enum classes close to where they are used, unless they are used across multiple classes (then put them at the top of the file)
* Use single double-quote docstrings (a string below the field definition) instead of comments to describe a field's purpose.
* Use `ModelName.foreign_key()` when generating a foreign key field

