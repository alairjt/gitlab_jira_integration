import os
from jira import JIRA
from jira.exceptions import JIRAError


class JiraClient:
    def __init__(self, config_manager, server=None, basic_auth=None):
        self.server = server or os.getenv("JIRA_SERVER")
        self.basic_auth = basic_auth or (os.getenv("JIRA_USER"), os.getenv("JIRA_TOKEN"))
        self.config_manager = config_manager
        self.version_path = os.getenv("VERSION_PATH")

        if not self.server:
            raise ValueError("Jira server URL is required.")
        if not self.basic_auth or not all(self.basic_auth):
            raise ValueError("Jira basic authentication (user email, API token) is required.")

        self.jira = JIRA(server=self.server, basic_auth=self.basic_auth)

    def add_comment(self, issue_key, comment):
        """
        Adds a comment to a Jira issue.
        """
        issue = self.jira.issue(issue_key)
        self.jira.add_comment(issue, comment)

    def _apply_template(self, text, variables):
        """Applies variables to a template string."""
        for key, value in variables.items():
            text = text.replace(f"{{{{ {key} }}}}", str(value))
        return text

    def _process_custom_field_value(self, value, variables):
        """Recursively processes custom field values to apply templates."""
        if isinstance(value, dict):
            return {k: self._process_custom_field_value(v, variables) for k, v in value.items()}
        if isinstance(value, list):
            return [self._apply_template(item, variables) for item in value]
        return self._apply_template(value, variables)

    def _create_issue_with_fallback(self, issue_dict):
        """
        Tries to create an issue, and if it fails due to invalid custom fields,
        it retries without them.
        """
        try:
            return self.jira.create_issue(fields=issue_dict)
        except JIRAError as e:
            raise

    def create_issue_from_template(self, template, variables):
        """
        Creates a Jira issue from a template.
        """
        project = template['project']
        summary = self._apply_template(template['summary'], variables)
        description = self._apply_template(template['description'], variables)
        issue_type_name = self.config_manager.get_issue_type(template['issue_type'])

        issue_type = next((t for t in self.jira.issue_types() if t.name == issue_type_name), None)

        issue_dict = {
            'project': {'key': project},
            'summary': summary,
            'description': description,
            'issuetype': {'id': issue_type.id},
        }

        if 'custom_fields' in template:
            for field, value in template['custom_fields'].items():
                issue_dict[field] = self._process_custom_field_value(value, variables)

        new_issue = self._create_issue_with_fallback(issue_dict)
        if 'subtasks' in template:
            for subtask_template in template['subtasks']:
                self.create_subtask_from_template(new_issue["key"], subtask_template, variables)

        return new_issue

    def create_subtask_from_template(self, parent_issue_key, template, variables):
        """
        Creates a Jira sub-task from a template.
        """
        name = template['name']
        summary = self._apply_template(template['summary'], variables)
        description = self._apply_template(template['description'], variables)

        version_path = os.path.join(self.version_path, variables.get('version', ''))
        if os.path.exists(version_path):
            for filename in os.listdir(version_path):
                extension = os.path.splitext(filename)[1][1:]
                if os.path.splitext(filename)[0].lower() == name.lower():
                    with open(os.path.join(version_path, filename), 'r') as f:
                        content = f.read()
                        if extension.lower() == 'sql':
                            content = "{code:sql}{{content}}{code}".replace("{{content}}", content)
                        description += '\n\n' + content
                    break

        issue_type_name = self.config_manager.get_issue_type(template['issue_type'])
        issue_type = next((t for t in self.jira.issue_types() if t.name == issue_type_name), None)
        parent_issue = self.jira.issue(parent_issue_key)

        issue_dict = {
            'project': {'key': parent_issue.fields.project.key},
            'summary': summary,
            'description': description,
            'issuetype': {'id': issue_type.id},
            'parent': {'id': parent_issue.id},
        }

        if 'custom_fields' in template:
            for field, value in template['custom_fields'].items():
                issue_dict[field] = self._process_custom_field_value(value, variables)
        
        new_issue = self._create_issue_with_fallback(issue_dict)
        return new_issue

    def get_version_url(self, project_key, version_name):
        """
        Gets the URL for a specific version in a project.
        """
        versions = self.jira.project_versions(project_key)
        for version in versions:
            if version.name.lower() == version_name.lower():
                return f"{self.server}/secure/ReleaseNote.jspa?projectId={version.projectId}&version={version.id}"
        return None
