# Target Known Variant

The user suspects the issue is in "feature_eng/builder.py in the feature building logic."

The agent is given the correct file location but must still:
1. Identify the specific anti-pattern (apply(axis=1) with row-wise functions)
2. Implement the vectorized solution
3. Validate correctness and performance

This tests the agent's ability to fix a known bottleneck location efficiently.
