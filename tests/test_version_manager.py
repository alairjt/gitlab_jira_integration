import pytest
from unittest.mock import mock_open, patch
from gitlab_jira_integration.version_manager import VersionManager

def test_get_version_success():
    with patch("builtins.open", mock_open(read_data="1.2.3")) as mock_file:
        with patch("os.path.exists", return_value=True):
            manager = VersionManager(version_file_path="VERSION")
            assert manager.get_version() == "1.2.3"

def test_get_version_file_not_found():
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            VersionManager(version_file_path="NON_EXISTENT_FILE")

def test_get_version_invalid_semver():
    with patch("builtins.open", mock_open(read_data="invalid-version")) as mock_file:
        with patch("os.path.exists", return_value=True):
            manager = VersionManager(version_file_path="VERSION")
            with pytest.raises(ValueError):
                manager.get_version()
