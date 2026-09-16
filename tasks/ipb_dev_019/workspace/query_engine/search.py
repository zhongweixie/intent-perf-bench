"""Search functionality for records."""


def search_records(records, query_terms):
    """Search records by text matching across multiple fields.

    Args:
        records: List of record dictionaries
        query_terms: List of search terms to match

    Returns:
        List of matching records
    """
    if not query_terms:
        return records

    matches = []
    for record in records:
        # Build searchable text from record fields
        searchable = ' '.join([
            str(record.get('name', '')),
            str(record.get('description', '')),
            str(record.get('category', '')),
            str(record.get('tags', []))
        ]).lower()

        # Check if all query terms match
        if all(term.lower() in searchable for term in query_terms):
            matches.append(record)

    return matches
