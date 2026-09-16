"""Report formatting module."""

def format_line(record):
    """Format a single record as a report line.

    Args:
        record: Dictionary containing record data

    Returns:
        Formatted string line
    """
    return f"{record['id']} | {record['timestamp']} | {record['value']:4d} | {record['status']:10s} | {record['category']}"


def generate_report(data):
    """Generate formatted report from data records.

    This implementation builds the report string incrementally for clarity.

    Args:
        data: List of record dictionaries

    Returns:
        Complete report as string
    """
    result = ""

    # Header
    result += "=" * 80 + "\n"
    result += "PERFORMANCE REPORT\n"
    result += "=" * 80 + "\n"
    result += "\n"
    result += f"Total Records: {len(data)}\n"
    result += "\n"
    result += "ID        | Timestamp            | Value | Status     | Category\n"
    result += "-" * 80 + "\n"

    # Data rows - incremental string building
    for record in data:
        result += format_line(record) + "\n"

    # Footer
    result += "-" * 80 + "\n"
    result += f"End of report ({len(data)} records processed)"

    return result
