"""Sample data generation for report testing."""

def generate_sample_data(num_records=500000):
    """Generate sample data records for report generation.

    Args:
        num_records: Number of records to generate

    Returns:
        List of dictionaries with record data
    """
    records = []
    for i in range(num_records):
        record = {
            'id': f'REC-{i:06d}',
            'timestamp': f'2026-08-{(i % 28) + 1:02d} {(i % 24):02d}:{(i % 60):02d}:00',
            'value': (i * 37) % 1000,
            'status': ['active', 'pending', 'completed', 'failed'][i % 4],
            'category': ['A', 'B', 'C', 'D', 'E'][i % 5]
        }
        records.append(record)
    return records
