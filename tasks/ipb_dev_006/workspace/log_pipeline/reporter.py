"""Log Reporter Module

Formats aggregated log data for display.
"""
import pandas as pd


class LogReporter:
    """Format log aggregation results for output."""

    def format_service_summary(self, service_summary: pd.DataFrame) -> str:
        """Format service-level summary as text."""
        lines = ["=== Service Summary ==="]
        for _, row in service_summary.iterrows():
            lines.append(
                f"  {row['service']:8s}: {int(row['event_count']):6d} events, "
                f"avg {row['avg_duration']:.1f}ms, "
                f"{int(row['error_count'])} errors"
            )
        return "\n".join(lines)

    def format_host_summary(self, host_summary: pd.DataFrame) -> str:
        """Format host-level summary."""
        total = host_summary['count'].sum()
        n_hosts = host_summary['host'].nunique()
        return (
            f"=== Host Summary ===\n"
            f"  Total events across {n_hosts} hosts: {total}"
        )
