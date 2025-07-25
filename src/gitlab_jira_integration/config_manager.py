import yaml
import os
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("CONFIG_PATH", ".gitlab-jira-integration.yml")
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Loads the YAML configuration file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Gets a specific template by name."""
        for template in self.config.get('templates', []):
            if template.get('name') == name:
                return template
        return None

    def get_issue_type(self, name: str) -> str:
        """Gets the issue type name from the configuration."""
        return self.config.get('issue_types', {}).get(name, name)
