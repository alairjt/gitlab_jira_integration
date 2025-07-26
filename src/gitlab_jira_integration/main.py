import os

from gitlab_jira_integration.gitlab_client import GitLabClient
from gitlab_jira_integration.jira_client import JiraClient
from gitlab_jira_integration.version_manager import VersionManager
from gitlab_jira_integration.config_manager import ConfigManager


def main():
    # Load configuration
    config_manager = ConfigManager()
    template_name = os.getenv("JIRA_TEMPLATE_NAME", "release_task")
    template = config_manager.get_template(template_name)

    if not template:
        print(f"Template '{template_name}' not found in the configuration.")
        return

    # Get version
    version_manager = VersionManager()
    version = version_manager.get_version()

    if not version:
        print("No version found.")
        return

    print(f"Version found: {version}")

    # Get Jira release notes URL
    jira_client = JiraClient(config_manager)
    project_key = os.getenv("JIRA_PROJECT_KEY")
    if not project_key:
        print("Jira project key not found.")
        return

    release_notes_url = jira_client.get_version_url(project_key, version)

    # Create a GitLab tag
    gitlab_client = GitLabClient()
    commit_sha = os.getenv("CI_COMMIT_SHA")
    if not commit_sha:
        print("Commit SHA not found.")
        return

    version = version.replace(" ", "").strip().lower()
    tag_message = f"Release version {version}"
    if release_notes_url:
        tag_message += f"\n\nRelease notes: {release_notes_url}"

    try:
        tag = gitlab_client.create_tag(version, commit_sha, message=tag_message)
        print(f"Created GitLab tag: {tag.name}")
    except Exception as e:
        print(f"Failed to create GitLab tag: {e}")
        # Decide if the process should stop if tag creation fails
        # For now, we'll just print the error and continue

    # Get merge request info from GitLab
    merge_request_iid = os.getenv("CI_MERGE_REQUEST_IID")
    if not merge_request_iid:
        print("Merge request IID not found.")
        return

    # Create a Jira issue
    application_id = os.getenv("JIRA_TASK_APPLICATION_ID")
    environment_id = os.getenv("JIRA_TASK_ENVIRONMENT_ID")
    if not application_id or not environment_id:
        print("Jira application ID or environment ID not found.")
        return
        
    variables = {
        "version": version,
        "application_id": application_id,
        "environment_id": environment_id,
        "release_notes_url": release_notes_url or ""
    }

    new_issue = jira_client.create_issue_from_template(
        template=template,
        variables=variables,
    )

    print(f"Created Jira issue: {new_issue.key}")

if __name__ == "__main__":
    main()
