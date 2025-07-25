import os
import semver
from typing import Optional

class VersionManager:
    def __init__(self, version_file_path: Optional[str] = None):
        self.version_file_path = version_file_path or os.getenv("VERSION_FILE_PATH", "VERSION")
        if not os.path.exists(self.version_file_path):
            raise FileNotFoundError(f"Version file not found at: {self.version_file_path}")

    def get_version(self) -> Optional[str]:
        """
        Gets the version from the VERSION file.
        """
        with open(self.version_file_path, 'r') as f:
            version = f.read().strip()
        
        return version