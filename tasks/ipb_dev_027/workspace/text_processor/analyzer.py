"""Text analysis and pattern counting."""


def count_patterns(texts, patterns):
    """Count occurrences of patterns in texts using case-insensitive literal matching.

    Patterns are matched as plain literal strings via str.count() on a
    lowercased copy of each text.  This is equivalent to re.findall with
    re.IGNORECASE for literal (non-regex) patterns and avoids all regex
    compilation and dispatch overhead.

    Args:
        texts: List of text strings
        patterns: List of pattern strings to search for

    Returns:
        Dictionary mapping pattern to count
    """
    # Lower-case the patterns once; texts are lowered inside the loop
    patterns_lower = [p.lower() for p in patterns]
    counts = {pattern: 0 for pattern in patterns}

    for text in texts:
        text_lower = text.lower()
        for pattern, pattern_lower in zip(patterns, patterns_lower):
            counts[pattern] += text_lower.count(pattern_lower)

    return counts


def extract_keywords(texts, min_length=4):
    """Extract keywords from texts with frequency counting.

    Args:
        texts: List of text strings
        min_length: Minimum keyword length

    Returns:
        Dictionary mapping keyword to frequency
    """
    keyword_freq = {}

    for text in texts:
        words = text.lower().split()
        for word in words:
            # Clean word
            word = word.strip('.,!?;:"\'()[]{}')
            if len(word) >= min_length:
                keyword_freq[word] = keyword_freq.get(word, 0) + 1

    return keyword_freq
