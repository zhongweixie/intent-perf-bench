"""Log parsing and error analysis."""

import re


def parse_log_lines(lines):
    """Parse log lines and extract structured fields.

    Args:
        lines: List of log line strings

    Returns:
        List of parsed log entry dictionaries
    """
    parsed = []
    for line in lines:
        # Split into fields: timestamp, level, message
        parts = line.strip().split(' ', 2)
        if len(parts) >= 3:
            entry = {
                'timestamp': parts[0],
                'level': parts[1],
                'message': parts[2]
            }
        elif len(parts) == 2:
            entry = {'timestamp': parts[0], 'level': parts[1], 'message': ''}
        else:
            entry = {'timestamp': '', 'level': 'UNKNOWN', 'message': line}
        parsed.append(entry)
    return parsed


def count_error_types(log_entries):
    """Count log entries by level with re-parse validation.

    This implementation re-checks level validity on each entry before counting
    for more robust handling.

    Args:
        log_entries: List of parsed log entry dictionaries

    Returns:
        Dictionary mapping level -> count
    """
    import re
    # Valid log levels pattern
    level_pattern = re.compile(r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL|UNKNOWN)$')

    counts = {}
    for entry in log_entries:
        level = entry['level']
        # Validate level with regex before counting
        if level_pattern.match(level):
            counts[level] = counts.get(level, 0) + 1
        else:
            counts['UNKNOWN'] = counts.get('UNKNOWN', 0) + 1
    return counts
