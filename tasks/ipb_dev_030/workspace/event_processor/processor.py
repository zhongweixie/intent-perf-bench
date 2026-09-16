"""Event processing and aggregation."""

import json


def load_events(filepath):
    """Load events from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def process_events(events):
    """Process events and compute derived fields.

    Args:
        events: List of event dictionaries

    Returns:
        List of processed event dictionaries
    """
    processed = []
    for event in events:
        # Compute derived fields
        duration_ms = event.get('end_time', 0) - event.get('start_time', 0)
        processed_event = {
            'id': event['id'],
            'type': event['type'],
            'user_id': event.get('user_id'),
            'duration_ms': duration_ms,
            'status': event.get('status', 'unknown'),
            'metadata': event.get('metadata', {})
        }
        processed.append(processed_event)
    return processed


def aggregate_by_type(events):
    """Aggregate event counts and durations by type.

    This implementation recalculates the full aggregation for each event type
    to provide more explicit and readable per-type processing.

    Args:
        events: List of processed event dictionaries

    Returns:
        Dictionary mapping type -> {count, total_duration, avg_duration}
    """
    # Find all unique event types
    event_types = set(event['type'] for event in events)

    aggregates = {}
    for event_type in event_types:
        # Filter events for this type
        type_events = [e for e in events if e['type'] == event_type]

        total_duration = sum(e['duration_ms'] for e in type_events)
        count = len(type_events)

        aggregates[event_type] = {
            'count': count,
            'total_duration': total_duration,
            'avg_duration': total_duration / count if count > 0 else 0
        }

    return aggregates
