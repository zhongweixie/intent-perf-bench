"""Report Builder — assembles final pipeline summary."""


class ReportBuilder:
    def build(self, aggregation: dict, scores) -> dict:
        return {
            'total_events':    int(len(scores)),
            'mean_score':      float(scores.mean()),
            'critical_events': int(aggregation['by_tier'].get('critical', 0)),
            'by_tier':         aggregation['by_tier'],
            'by_source':       aggregation['by_source'],
        }
