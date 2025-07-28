import pytest
import os
from unittest.mock import MagicMock, patch, mock_open

from gitlab_jira_integration.jira_client import JiraClient
from gitlab_jira_integration.config_manager import ConfigManager

@pytest.fixture
def mock_config_manager():
    """Fixture for a mocked ConfigManager."""
    mock = MagicMock(spec=ConfigManager)
    mock.get_issue_type.side_effect = lambda x: x  # Return the same name passed
    return mock

@pytest.fixture
def jira_client(mock_config_manager):
    """Fixture for a mocked JiraClient."""
    with patch.dict('os.environ', {
        'JIRA_URL': 'https://jira.example.com',
        'JIRA_USER': 'user@example.com',
        'JIRA_TOKEN': 'token'
    }), patch('gitlab_jira_integration.jira_client.JIRA') as mock_jira_class:
        
        mock_jira_instance = MagicMock()
        
        # Mock issue types
        mock_issue_type_task = MagicMock()
        mock_issue_type_task.name = 'Task'
        mock_issue_type_task.id = '10001'
        
        mock_issue_type_subtask = MagicMock()
        mock_issue_type_subtask.name = 'Sub-task'
        mock_issue_type_subtask.id = '10002'

        mock_jira_instance.issue_types.return_value = [mock_issue_type_task, mock_issue_type_subtask]

        # Mock issue creation
        mock_created_issue = MagicMock()
        mock_created_issue.key = 'PROJ-123'
        
        mock_parent_issue = MagicMock()
        mock_parent_issue.key = 'PROJ-123'
        mock_parent_issue.id = '100'
        mock_parent_issue.fields.project.key = 'PROJ'

        mock_jira_instance.create_issue.return_value = mock_created_issue
        mock_jira_instance.issue.return_value = mock_parent_issue

        mock_jira_class.return_value = mock_jira_instance
        
        client = JiraClient(config_manager=mock_config_manager)
        yield client

def test_create_subtask_with_version_file_content(jira_client):
    """
    Tests if a subtask is created with its description appended with
    content from a version file.
    """
    parent_issue_key = 'PROJ-123'
    template = {
        'summary': 'My Subtask',
        'description': 'Initial description.',
        'issue_type': 'Sub-task'
    }
    variables = {
        'VERSION': '1.0.0'
    }

    version_content = "Content from version file."
    version_file_path = '/home/alairjt/workspace/suportly/gitlab-jira-integration/tests/versions/1.0.0/my subtask.txt'
    
    # Mocks for os.path.exists, os.listdir, and open
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir, \
         patch('builtins.open', mock_open(read_data=version_content)) as mock_file:

        mock_exists.return_value = True
        mock_listdir.return_value = ['my subtask.txt']

        jira_client.create_subtask_from_template(parent_issue_key, template, variables)

        # Verify that the file was opened
        mock_file.assert_called_once_with(version_file_path, 'r')

        # Verify that create_issue was called with the correct description
        final_description = 'Initial description.\n\n' + version_content
        
        call_args = jira_client.jira.create_issue.call_args
        assert call_args is not None
        
        fields = call_args[1]['fields']
        assert fields['summary'] == 'My Subtask'
        assert fields['description'] == final_description
        assert fields['parent']['id'] == '100'

def test_create_issue_and_subtasks(jira_client):
    """
    Tests the creation of a main issue and its subtasks, where one subtask
    has its description modified by a version file.
    """
    template = {
        'project': 'PROJ',
        'summary': 'Main Task {{ version }}',
        'description': 'Main description.',
        'issue_type': 'Task',
        'subtasks': [
            {
                'summary': 'Subtask One',
                'description': 'Description for subtask one.',
                'issue_type': 'Sub-task'
            },
            {
                'summary': 'Subtask Two',
                'description': 'Description for subtask two.',
                'issue_type': 'Sub-task'
            }
        ]
    }
    variables = {
        'version': '1.0.0'
    }

    version_content = "Dynamic content for subtask two."
    version_file_path = '/home/alairjt/workspace/suportly/gitlab-jira-integration/tests/versions/1.0.0/subtask two.txt'

    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir, \
         patch('builtins.open', mock_open(read_data=version_content)) as mock_file:
        
        # Simulate that the version file exists only for 'Subtask Two'
        def side_effect(path):
            return '1.0.0' in path

        mock_exists.side_effect = side_effect
        mock_listdir.return_value = ['subtask two.txt']

        # --- Function Call ---
        jira_client.create_issue_from_template(template, variables)

        # --- Assertions ---
        
        # Check main issue creation
        main_issue_call_args = jira_client.jira.create_issue.call_args_list[0]
        main_issue_fields = main_issue_call_args[1]['fields']
        assert main_issue_fields['summary'] == 'Main Task 1.0.0'

        # Check subtask creations
        subtask_calls = jira_client.jira.create_issue.call_args_list[1:]
        assert len(subtask_calls) == 2

        # Assert Subtask One (no version file)
        subtask_one_fields = subtask_calls[0][1]['fields']
        assert subtask_one_fields['summary'] == 'Subtask One'
        assert subtask_one_fields['description'] == 'Description for subtask one.'

        # Assert Subtask Two (with version file)
        subtask_two_fields = subtask_calls[1][1]['fields']
        assert subtask_two_fields['summary'] == 'Subtask Two'
        assert subtask_two_fields['description'] == 'Description for subtask two.\n\n' + version_content
        
        # Verify that the file for subtask two was opened
        mock_file.assert_called_with(version_file_path, 'r')