import pytest
from unittest.mock import MagicMock, patch
from gitlab_jira_integration.jira_client import JiraClient

@pytest.fixture
def jira_client(mocker):
    mocker.patch.dict('os.environ', {
        'JIRA_SERVER': 'https://jira.example.com',
        'JIRA_USER_EMAIL': 'test@example.com',
        'JIRA_API_TOKEN': 'test_token'
    })
    mock_config_manager = MagicMock()
    # Make get_issue_type return the same name it received for simplicity in this test
    mock_config_manager.get_issue_type.side_effect = lambda name: name

    with patch('gitlab_jira_integration.jira_client.JIRA') as mock_jira:
        client = JiraClient(config_manager=mock_config_manager)
        client.jira = mock_jira.return_value
        yield client

def test_create_issue_from_template_with_custom_fields(jira_client):
    template = {
        'summary': 'Test Summary - {{ version }}',
        'description': 'Test Description - {{ version }}',
        'issue_type': 'Task',
        'custom_fields': {
            'customfield_10060': '{{ application }}',
            'customfield_10482': '{{ release_notes_url }}'
        }
    }
    variables = {
        'version': '1.0.0',
        'application': 'MyTestApp',
        'release_notes_url': 'http://example.com/notes/1.0.0'
    }
    
    mock_issue = MagicMock()
    mock_issue.key = 'PROJ-123'
    jira_client.jira.create_issue.return_value = mock_issue

    issue = jira_client.create_issue_from_template('PROJ', template, variables)

    jira_client.jira.create_issue.assert_called_with(fields={
        'project': {'key': 'PROJ'},
        'summary': 'Test Summary - 1.0.0',
        'description': 'Test Description - 1.0.0',
        'issuetype': {'name': 'Task'},
        'customfield_10060': 'MyTestApp',
        'customfield_10482': 'http://example.com/notes/1.0.0'
    })
    assert issue.key == 'PROJ-123'
