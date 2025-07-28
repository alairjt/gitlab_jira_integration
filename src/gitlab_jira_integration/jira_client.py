import os
from typing import Dict, Any, Optional, Union, List
from jira import JIRA
from jira.exceptions import JIRAError
from .test_mode import test_logger


class JiraClient:
    def __init__(self, config_manager, server=None, basic_auth=None):
        self.server = server or os.getenv("JIRA_URL")
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

    def create_issue_from_template(self, template: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a Jira issue from a template.
        In test mode, logs the operation instead of creating the issue.
        
        Args:
            template: Issue template with fields and configuration
            variables: Variables to apply to the template
            
        Returns:
            Dict containing the created issue or test mode response
        """
        project = template['project']
        summary = self._apply_template(template['summary'], variables)
        description = self._apply_template(template['description'], variables)
        issue_type_name = self.config_manager.get_issue_type(template['issue_type'])
        
        # Prepare operation details for logging
        operation_details = {
            'project': project,
            'summary': summary,
            'description': description,
            'issue_type': issue_type_name,
            'template_name': template.get('name', 'unknown'),
            'variables': variables
        }
        
        if test_logger.is_enabled():
            test_response = {
                'key': 'TEST-ISSUE-KEY',
                'fields': {
                    'summary': summary,
                    'description': description,
                    'project': {'key': project},
                    'issuetype': {'name': issue_type_name}
                },
                'test_mode': True
            }
            
            # Log the test issue creation
            test_logger.log_operation('create_issue', operation_details)
            
            # Process subtasks if any (even in test mode)
            if 'subtasks' in template:
                for subtask_template in template['subtasks']:
                    self.create_subtask_from_template(test_response['key'], subtask_template, variables)
            
            return test_response

        # In normal mode, create the actual issue
        try:
            issue_type = next((t for t in self.jira.issue_types() if t.name == issue_type_name), None)
            if not issue_type:
                raise ValueError(f"Issue type '{issue_type_name}' not found")

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
            
            # Log successful creation
            operation_details['issue_key'] = new_issue.key
            test_logger.log_operation('create_issue', operation_details)
            
            # Process subtasks if any
            if 'subtasks' in template:
                for subtask_template in template['subtasks']:
                    self.create_subtask_from_template(new_issue.key, subtask_template, variables)
            
            return new_issue
            
        except Exception as e:
            operation_details['error'] = str(e)
            test_logger.log_operation('create_issue_error', operation_details)
            raise

    def create_subtask_from_template(self, parent_issue_key: str, template: Dict[str, Any], 
                                   variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Creates a Jira sub-task from a template.
        Only creates the subtask if require_file is False or if the file exists.
        In test mode, logs the operation instead of creating the subtask.
        
        Args:
            parent_issue_key: Key of the parent issue
            template: Subtask template with fields and configuration
            variables: Variables to apply to the template
            
        Returns:
            Dict containing the created subtask or None if skipped/not created
        """
        name = template['name']
        summary = self._apply_template(template['summary'], variables)
        description = self._apply_template(template['description'], variables)
        require_file = template.get('require_file', False)
        file_found = False
        file_content = ""

        # Check for matching files in version directory
        version_path = os.path.join(self.version_path, variables.get('version', ''))
        if os.path.exists(version_path):
            for filename in os.listdir(version_path):
                if os.path.splitext(filename)[0].lower() == name.lower():
                    file_found = True
                    extension = os.path.splitext(filename)[1][1:]
                    with open(os.path.join(version_path, filename), 'r') as f:
                        file_content = f.read()
                        if extension.lower() == 'sql':
                            file_content = "{code:sql}{{content}}{code}".replace("{{content}}", file_content)
                        description += '\n\n' + file_content
                    break

        # Prepare operation details for logging
        operation_details = {
            'parent_issue_key': parent_issue_key,
            'name': name,
            'summary': summary,
            'description': description,
            'require_file': require_file,
            'file_found': file_found,
            'file_content': file_content if file_found else "",
            'template': template
        }

        # Skip subtask creation if require_file is True and no matching file was found
        if require_file and not file_found:
            skip_message = f"Skipping subtask '{name}' - no matching file found in version directory"
            print(skip_message)
            operation_details['skipped'] = True
            operation_details['skip_reason'] = 'file_not_found'
            test_logger.log_operation('skip_subtask', operation_details)
            return None
            
        # In test mode, log the operation and return a test response
        if test_logger.is_enabled():
            # Generate a test subtask key based on parent issue key
            test_subtask_key = f"{parent_issue_key.replace('TEST-', '')}-{name.upper().replace(' ', '-')}"
            test_response = {
                'key': test_subtask_key,
                'fields': {
                    'summary': summary,
                    'description': description,
                    'parent': {'key': parent_issue_key},
                    'issuetype': {'name': template.get('issue_type', 'Sub-task')}
                },
                'test_mode': True
            }
            operation_details['test_response'] = test_response
            test_logger.log_operation('create_subtask', operation_details)
            return test_response
            
        # In normal mode, create the actual subtask
        try:
            # Log the operation details before attempting to create
            test_logger.log_operation('create_subtask', operation_details)
            issue_type_name = self.config_manager.get_issue_type(template['issue_type'])
            issue_type = next((t for t in self.jira.issue_types() if t.name == issue_type_name), None)
            if not issue_type:
                raise ValueError(f"Issue type '{issue_type_name}' not found")
                
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
            
            # Log successful creation
            operation_details['subtask_key'] = new_issue.key
            test_logger.log_operation('create_subtask', operation_details)
            
            return new_issue
            
        except Exception as e:
            operation_details['error'] = str(e)
            test_logger.log_operation('create_subtask_error', operation_details)
            raise

    def get_version_url(self, project_key, version_name):
        """
        Gets the URL for a specific version in a project.
        """
        versions = self.jira.project_versions(project_key)
        for version in versions:
            if version.name.lower() == version_name.lower():
                return f"{self.server}/secure/ReleaseNote.jspa?projectId={version.projectId}&version={version.id}"
        return None
