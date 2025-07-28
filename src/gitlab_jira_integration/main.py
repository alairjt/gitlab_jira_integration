import os
import sys
from typing import Optional, Dict, Any

from gitlab_jira_integration.gitlab_client import GitLabClient
from gitlab_jira_integration.jira_client import JiraClient
from gitlab_jira_integration.version_manager import VersionManager
from gitlab_jira_integration.config_manager import ConfigManager
from gitlab_jira_integration.test_mode import test_logger

def print_environment_info():
    """Print information about the current environment and configuration."""
    print("\n" + "="*50)
    print("GitLab-Jira Integration Tool")
    print("="*50)
    print(f"Environment:")
    print(f"  - Python: {sys.version.split()[0]}")
    print(f"  - Working directory: {os.getcwd()}")
    print(f"  - Test mode: {'ENABLED' if test_logger.is_enabled() else 'DISABLED'}")
    print("-"*50)

    # Print important environment variables
    env_vars = [
        'CI_PROJECT_ID', 'CI_COMMIT_REF_NAME', 'CI_COMMIT_SHA', 'JIRA_PROJECT_KEY'
    ]

    print("Environment variables:")
    for var in env_vars:
        value = os.getenv(var, 'Not set')
        print(f"  - {var}: {value}")
    
    print("="*50 + "\n")


def main():
    # Print environment information
    print_environment_info()

    # Load configuration
    config_manager = ConfigManager()
    template_name = os.getenv("JIRA_TEMPLATE_NAME", "release_task")
    template = config_manager.get_template(template_name)

    if not template:
        error_msg = f"Template '{template_name}' not found in the configuration."
        print(error_msg)
        test_logger.log_operation('error', {'message': error_msg})
        return 1

    # Get version
    version_manager = VersionManager()
    version = version_manager.get_version()

    if not version:
        error_msg = "No version found in VERSION file."
        print(error_msg)
        test_logger.log_operation('error', {'message': error_msg})
        return 1

    print(f"Version found: {version}")

    # Get Jira release notes URL
    jira_client = JiraClient(config_manager)
    project_key = os.getenv("JIRA_PROJECT_KEY")
    if not project_key:
        error_msg = "Jira project key not found. Set JIRA_PROJECT_KEY environment variable."
        print(error_msg)
        test_logger.log_operation('error', {'message': error_msg})
        return 1

    release_notes_url = jira_client.get_version_url(project_key, version)
    if release_notes_url:
        print(f"Release notes URL: {release_notes_url}")

    # Create a GitLab tag
    gitlab_client = GitLabClient()
    commit_sha = os.getenv("CI_COMMIT_SHA")
    if not commit_sha:
        error_msg = "Commit SHA not found. Set CI_COMMIT_SHA environment variable."
        print(error_msg)
        test_logger.log_operation('error', {'message': error_msg})
        return 1

    version = version.replace(" ", "").strip().lower()
    tag_message = f"Release version {version}"
    if release_notes_url:
        tag_message += f"\n\nRelease notes: {release_notes_url}"

    try:
        tag = gitlab_client.create_tag(version, commit_sha, message=tag_message)
        if test_logger.is_enabled():
            print(f"[TEST MODE] Would create GitLab tag: {version}")
        else:
            print(f"Created GitLab tag: {tag.name}")
    except Exception as e:
        error_msg = f"Failed to create GitLab tag: {e}"
        print(error_msg)
        test_logger.log_operation('error', {'message': error_msg, 'version': version})
        # Continue execution even if tag creation fails

    # Create a Jira issue
    application_id = os.getenv("JIRA_TASK_APPLICATION_ID")
    environment_id = os.getenv("JIRA_TASK_ENVIRONMENT_ID")
    if not application_id or not environment_id:
        error_msg = "Jira application ID or environment ID not found. Set JIRA_TASK_APPLICATION_ID and JIRA_TASK_ENVIRONMENT_ID environment variables."
        print(error_msg)
        test_logger.log_operation('error', {'message': error_msg})
        return 1
        
    variables = {
        "version": version,
        "application_id": application_id,
        "environment_id": environment_id,
        "release_notes_url": release_notes_url or ""
    }

    try:
        new_issue = jira_client.create_issue_from_template(
            template=template,
            variables=variables,
        )
        
        if test_logger.is_enabled():
            print(f"[TEST MODE] Would create Jira issue: {new_issue['key']}")
        else:
            print(f"Created Jira issue: {new_issue.key}")
            
        return 0
        
    except Exception as e:
        error_msg = f"Failed to create Jira issue: {e}"
        print(error_msg)
        test_logger.log_operation('error', {
            'message': error_msg,
            'template': template_name,
            'version': version
        })
        return 1

if __name__ == "__main__":
    main()
