"""Log Formatter Module - REGRESSED VERSION

Formats structured logs into human-readable text.

REGRESSION: Repeatedly joins entire list on each iteration
"""


class LogFormatter:
    """Format structured logs into human-readable text."""

    def format_logs(self, logs: list) -> str:
        """
        Format log entries into readable text.

        SLOW: joins entire list every iteration instead of once at end.
        """
        lines = []
        for log in logs:
            line = f"[{log['timestamp']}] {log['level']:5s} {log['service']:12s} | {log['message']} (user={log['user_id']}, req={log['request_id']})\n"
            lines.append(line)
            # Anti-pattern: rebuild entire string on each iteration O(n^2)
            result = "".join(lines)
        return result
