"""Log Loader Module

Loads structured log entries from JSON format.
"""
import json
import time
import pandas as pd


class LogLoader:
    """Load structured logs from JSON."""

    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def load_logs(self, n_logs: int = 30000) -> list:
        """Load raw JSON log entries. Simulates I/O latency."""
        if self.simulate_io:
            # Simulate realistic JSON file I/O
            time.sleep(1.20)

        # Generate synthetic structured logs
        logs = []
        for i in range(n_logs):
            logs.append({
                'timestamp': f'2024-01-01T{i%24:02d}:{i%60:02d}:00Z',
                'level': ['INFO', 'WARN', 'ERROR', 'DEBUG'][i % 4],
                'service': f'service-{i % 8}',
                'message': f'Event {i} occurred',
                'user_id': f'user_{i % 100}',
                'request_id': f'req_{i}',
            })
        return logs
