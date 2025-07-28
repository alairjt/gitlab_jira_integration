import gitlab
import os
from typing import Optional, Dict, Any
from .test_mode import test_logger

class GitLabClient:
    def __init__(self, private_token=None, project_id=None, url=None):
        self.url = url or os.getenv("CI_SERVER_URL")
        self.private_token = private_token or os.getenv("GITLAB_TOKEN")
        self.project_id = project_id or os.getenv("CI_PROJECT_ID")

        if not self.private_token:
            raise ValueError("GitLab private token is required.")
        if not self.project_id:
            raise ValueError("GitLab project ID is required.")

        self.gl = gitlab.Gitlab(self.url, private_token=self.private_token)
        self.project = self.gl.projects.get(self.project_id)

    def get_merge_request_diff(self, merge_request_iid):
        """
        Gets the diff of a merge request.
        """
        mr = self.project.mergerequests.get(merge_request_iid)
        return mr.diffs.list()

    def get_merge_request_changes(self, merge_request_iid):
        """
        Gets the changes of a merge request.
        """
        mr = self.project.mergerequests.get(merge_request_iid)
        return mr.changes()

    def create_tag(self, tag_name: str, ref: str, message: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a new tag in the project.
        In test mode, logs the operation instead of creating the tag.
        
        Args:
            tag_name: Name of the tag to create
            ref: Git reference (commit SHA) to tag
            message: Optional message for the tag
            
        Returns:
            Dict containing tag information or test mode response
        """
        tag_name = tag_name.replace(' ', '').strip().lower()
        tag_data = {
            'tag_name': tag_name,
            'ref': ref,
            'message': message or f"Release version {tag_name}"
        }
        
        # Log the operation
        operation_details = {
            'tag_name': tag_name,
            'ref': ref,
            'message': tag_data['message'],
            'project_id': self.project_id
        }
        
        if test_logger.is_enabled():
            test_logger.log_operation('create_tag', operation_details)
            return {
                'name': tag_name,
                'message': 'Tag creation skipped - test mode',
                'test_mode': True
            }
            
        # In normal mode, actually create the tag
        try:
            tag = self.project.tags.create(tag_data)
            operation_details['created'] = True
            test_logger.log_operation('create_tag', operation_details)
            return tag
        except Exception as e:
            operation_details['error'] = str(e)
            test_logger.log_operation('create_tag_error', operation_details)
            raise
