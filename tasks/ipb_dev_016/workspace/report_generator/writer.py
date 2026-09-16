"""Report output module."""

def write_report(report_text, filename='output_report.txt'):
    """Write report text to file.

    Args:
        report_text: Complete report as string
        filename: Output filename

    Returns:
        Path to written file
    """
    with open(filename, 'w') as f:
        f.write(report_text)
    return filename
