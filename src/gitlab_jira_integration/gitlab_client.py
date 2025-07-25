import gitlab
import os

class GitLabClient:
    def __init__(self, private_token=None, project_id=None, url=None):
        self.url = url or os.getenv("CI_SERVER_URL")
        self.private_token = private_token or os.getenv("GITLAB_PRIVATE_TOKEN")
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

    def create_tag(self, tag_name, ref, message=None):
        """
        Creates a new tag in the project.
        """
        tag_name = tag_name.replace(' ', '').strip().lower()
        tag_data = {
            'tag_name': tag_name,
            'ref': ref,
            'message': message or f"Release version {tag_name}"
        }
        tag = self.project.tags.create(tag_data)
        return tag
