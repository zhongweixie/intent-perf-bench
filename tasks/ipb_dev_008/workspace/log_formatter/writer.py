"""Log Writer Module

Writes formatted logs to output file.
"""


class LogWriter:
    """Write formatted logs to file."""

    def write_logs(self, content: str, output_path: str = '/tmp/formatted_logs.txt') -> None:
        """Write formatted log content to file."""
        with open(output_path, 'w') as f:
            f.write(content)
