# GitLab Jira Integration

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Version](https://img.shields.io/pypi/v/gitlab-jira-integration.svg)](https://pypi.org/project/gitlab-jira-integration/)

Automate Jira issue and subtask creation from GitLab CI/CD pipelines with dynamic content population from versioned files.

## ✨ Features

- **Template-based** issue and subtask creation in Jira
- **Version-aware** content population from files
- **Test mode** for safe validation of issue creation
- **CI/CD ready** with comprehensive environment variable support
- **Detailed reporting** of all operations in test mode

## 🚀 Quick Start

### Installation

```bash
pip install gitlab-jira-integration
```

### Basic Usage

```bash
# Run in production mode
gitlab-jira-integration

# Run in test mode (no changes made, generates report)
export TEST_MODE=true
gitlab-jira-integration
```

## 📋 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JIRA_URL` | ✅ | URL of your Jira instance |
| `JIRA_USER` | ✅ | Jira username or email |
| `JIRA_TOKEN` | ✅ | Jira API token |
| `GITLAB_TOKEN` | ✅ | GitLab personal access token |
| `VERSION` | ✅ | Version to use for file lookups |
| `VERSION_PATH` | ❌ | Base directory for version files (default: `./versions`) |
| `TEST_MODE` | ❌ | Set to `true` to enable test mode (default: `false`) |
| `CI_PROJECT_ID` | Auto | GitLab project ID |
| `CI_COMMIT_REF_NAME` | Auto | Git branch/tag name |
| `CI_COMMIT_SHA` | Auto | Git commit SHA |

### Configuration File

Create a `.gitlab-jira-integration.yml` file in your project root:

```yaml
issue_types:
  RA: Release Automation
  Task: Task

templates:
  - name: release_task
    project: GMA
    issue_type: RA
    summary: "Atualizacao da aplicacao +Capital - {{ version }}"
    description: |
      h2. Atualizacao da aplicacao +Capital - {{ version }}

      *Release notes:*
      {{ release_notes_url }}
    custom_fields:
      customfield_10092: "{{ application_id }}"  # Application
      customfield_10093: "{{ environment_id }}"  # Environment
    subtasks:
      - name: "Deploy Frontend"
        summary: "[{{ version }}] Deploy Frontend"
        description: "Deploy the frontend application"
        issue_type: Task
        require_file: true
      - name: "Run Migrations"
        summary: "[{{ version }}] Run Database Migrations"
        description: "Execute database migrations"
        issue_type: Task
        require_file: false
```

## 🔍 How It Works

1. **Issue Creation**: Creates a main Jira issue using the specified template
2. **File Lookup**: For each subtask with `require_file: true`:
   - Looks in `VERSION_PATH/VERSION/` for files matching the subtask name
   - Case-insensitive matching (e.g., "Deploy Frontend" matches "deploy_frontend.md")
3. **Subtask Creation**: Creates subtasks, injecting file content when available
4. **Test Mode**: When enabled:
   - No actual API calls to Jira/GitLab
   - Generates `jira_integration_report.md` with all operations

### Example Report

```markdown
# GitLab-Jira Integration Report

**Test Mode**: ✅ Enabled  
**Generated at**: 2025-07-28T14:30:45.123456

## Create Issue Operations

### Operation 1 - 2025-07-28T14:30:45.123456
```json
{
  "project": "GMA",
  "summary": "Atualizacao da aplicacao +Capital - v1.2.3",
  "description": "h2. Atualizacao da aplicacao - v1.2.3\n\n*Release notes:*\nhttps://jira.example.com/release/1.2.3",
  "issue_type": "Release Automation"
}
```

## Create Subtask Operations

### Operation 1 - 2025-07-28T14:30:45.234567
```json
{
  "parent_issue_key": "GMA-123",
  "name": "Deploy Frontend",
  "summary": "[v1.2.3] Deploy Frontend",
  "file_found": true,
  "file_content": "Steps to deploy frontend..."
}
```

## 🛠️ Development

### Installation from Source

```bash
git clone https://github.com/alairjt/gitlab-jira-integration.git
cd gitlab-jira-integration
pip install -e .
```

### Running Tests

```bash
pip install -e ".[test]"
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

Alair Junior - [@alairjt](https://github.com/alairjt) - alairjt@gmail.com