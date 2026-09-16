import cProfile
import pstats
import sys
from io import StringIO

sys.path.insert(0, 'repo')
from scripts import daily_report

# Run with profiling
pr = cProfile.Profile()
pr.enable()

daily_report.main()

pr.disable()

# Print stats
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(20)
print(s.getvalue())
