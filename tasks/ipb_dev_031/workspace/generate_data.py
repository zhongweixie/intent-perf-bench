#!/usr/bin/env python3
"""Generate test log data."""

import random

def generate_log_lines(num_lines=200000):
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    # Uneven distribution
    weights = [10, 60, 20, 8, 2]
    messages = [
        "Request processed successfully",
        "Connection timeout occurred",
        "Cache miss for key",
        "Database query executed",
        "Invalid input received",
        "User authentication failed",
        "Service started",
        "Service stopped",
        "Configuration loaded",
        "Memory usage high"
    ]
    lines = []
    for i in range(num_lines):
        ts = f"2026-08-13T{(i//3600)%24:02d}:{(i//60)%60:02d}:{i%60:02d}.{i%1000:03d}Z"
        level = random.choices(levels, weights=weights)[0]
        msg = random.choice(messages)
        lines.append(f"{ts} {level} {msg}")
    return lines

if __name__ == '__main__':
    print("Generating log data...")
    lines = generate_log_lines(200000)
    with open('test_logs.txt', 'w') as f:
        f.write('\n'.join(lines))
    print(f"Generated {len(lines)} log lines -> test_logs.txt")
