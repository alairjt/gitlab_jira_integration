import os
import datetime
from typing import List, Dict, Any

class TestModeLogger:
    def __init__(self, output_file: str = "jira_integration_report.md"):
        """
        Initialize the test mode logger.
        
        Args:
            output_file: Path to the output markdown file
        """
        self.output_file = output_file
        self.operations: List[Dict[str, Any]] = []
        self.is_test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
    def log_operation(self, op_type: str, details: Dict[str, Any]) -> None:
        """
        Log an operation that would be performed in normal mode.
        
        Args:
            op_type: Type of operation (e.g., 'create_tag', 'create_issue', 'create_subtask')
            details: Dictionary containing operation details
        """
        self.operations.append({
            "type": op_type,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "details": details
        })
        
        # Always write to the log file immediately
        self._write_report()
    
    def _write_report(self) -> None:
        """Write the current operations to the markdown report file."""
        try:
            with open(self.output_file, 'w') as f:
                f.write(self._generate_markdown())
        except Exception as e:
            print(f"Warning: Failed to write test mode report: {e}")
    
    def _generate_markdown(self) -> str:
        """Generate the markdown content for the report."""
        lines = [
            "# GitLab-Jira Integration Report",
            f"**Generated at:** {datetime.datetime.utcnow().isoformat()}",
            f"**Test Mode:** {'✅ Enabled' if self.is_test_mode else '❌ Disabled'}",
            ""
        ]
        
        # Group operations by type
        ops_by_type = {}
        for op in self.operations:
            ops_by_type.setdefault(op['type'], []).append(op)
        
        # Add sections for each operation type
        for op_type, ops in ops_by_type.items():
            lines.append(f"## {op_type.replace('_', ' ').title()} Operations ({len(ops)})")
            
            for i, op in enumerate(ops, 1):
                lines.append(f"### Operation {i} - {op['timestamp']}")
                
                # Format details as a code block
                import json
                details_str = json.dumps(op['details'], indent=2, ensure_ascii=False)
                lines.append(f"```json\n{details_str}\n```")
                
                # Add a separator between operations
                if i < len(ops):
                    lines.append("---")
            
            # Add a separator between sections
            lines.append("\n")
        
        return "\n".join(lines)
    
    def is_enabled(self) -> bool:
        """Check if test mode is enabled."""
        return self.is_test_mode

# Global instance
test_logger = TestModeLogger()
