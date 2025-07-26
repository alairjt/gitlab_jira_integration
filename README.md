# GitLab JIRA Integration

This tool automates the creation of Jira issues and subtasks based on templates, with the ability to dynamically populate subtask descriptions from version-specific files.

## Features

- Create Jira issues from predefined templates.
- Automatically create subtasks associated with the main issue.
- Dynamically populate subtask descriptions with content from files stored in a versioned directory structure.
- Use variables (like version, application name, etc.) to customize issues and subtasks.

## How it Works

The integration uses a YAML configuration file (`.gitlab-jira-integration.yml`) to define templates for Jira issues and their corresponding subtasks.

When a new issue is created using a template:

1.  A main issue is created in Jira based on the template's `summary`, `description`, and other fields.
2.  For each entry in the `subtasks` list of the template, a corresponding subtask is created under the main issue.
3.  The tool then looks for a directory under `tests/versions/` that matches the `VERSION` variable provided.
4.  Inside that version directory, it searches for a file whose name (excluding the extension) is a case-insensitive match for the subtask's summary.
5.  If a matching file is found, its content is appended to that subtask's description.

### Example Workflow

1.  You have a subtask template with the summary: `Deploy Frontend Application`.
2.  You trigger the process with the version `2.5.1`.
3.  The tool will look in the directory: `tests/versions/2.5.1/`.
4.  It will search for a file like `deploy frontend application.txt`, `Deploy Frontend Application.md`, etc.
5.  If found, the contents of that file are added to the description of the "Deploy Frontend Application" subtask in Jira.

## Configuration

See the `.gitlab-jira-integration.example.yml` file for a detailed example of how to configure your templates and issue types.

## Usage

The main entry point is the `JiraClient` class, which can be used to create issues from your defined templates. You will need to provide the necessary variables (like `VERSION`) when calling it.