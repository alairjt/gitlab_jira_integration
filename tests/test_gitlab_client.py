import pytest
from unittest.mock import MagicMock, patch
from gitlab_jira_integration.gitlab_client import GitLabClient

@pytest.fixture
def gitlab_client(mocker):
    mocker.patch.dict('os.environ', {
        'GITLAB_URL': 'https://gitlab.example.com',
        'GITLAB_TOKEN': 'test_token',
        'CI_PROJECT_ID': '123'
    })
    with patch('gitlab.Gitlab') as mock_gitlab:
        mock_project = MagicMock()
        mock_gitlab.return_value.projects.get.return_value = mock_project
        client = GitLabClient()
        client.project = mock_project
        yield client

def test_create_tag(gitlab_client):
    mock_tag = MagicMock()
    mock_tag.name = 'v1.0.0'
    gitlab_client.project.tags.create.return_value = mock_tag
    tag = gitlab_client.create_tag('v1.0.0', 'abcdef123456')
    gitlab_client.project.tags.create.assert_called_with({
        'tag_name': 'v1.0.0',
        'ref': 'abcdef123456',
        'message': 'Release version v1.0.0'
    })
    assert tag.name == 'v1.0.0'

def test_get_merge_request_changes(gitlab_client):
    mock_mr = MagicMock()
    mock_mr.changes.return_value = {'changes': '...'}
    gitlab_client.project.mergerequests.get.return_value = mock_mr
    changes = gitlab_client.get_merge_request_changes(1)
    gitlab_client.project.mergerequests.get.assert_called_with(1)
    assert changes == {'changes': '...'}
