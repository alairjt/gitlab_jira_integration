import pytest
from unittest.mock import mock_open, patch
from gitlab_jira_integration.config_manager import ConfigManager

CONFIG_CONTENT = """
issue_types:
  default: Task
  release: Release

templates:
  - name: release_task
    issue_type: release
    summary: "Release version {{ version }}"
    description: "Release of version {{ version }}"
"""

def test_config_manager_success():
    with patch("builtins.open", mock_open(read_data=CONFIG_CONTENT)) as mock_file:
        with patch("os.path.exists", return_value=True):
            manager = ConfigManager(config_path=".gitlab-jira-integration.yml")
            template = manager.get_template("release_task")
            assert template is not None
            assert template["summary"] == "Release version {{ version }}"
            assert manager.get_issue_type("release") == "Release"

def test_config_manager_file_not_found():
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            ConfigManager(config_path="NON_EXISTENT_FILE")

def test_get_template_not_found():
    with patch("builtins.open", mock_open(read_data=CONFIG_CONTENT)) as mock_file:
        with patch("os.path.exists", return_value=True):
            manager = ConfigManager(config_path=".gitlab-jira-integration.yml")
            assert manager.get_template("non_existent_template") is None
