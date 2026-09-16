"""
Performance Benchmark Suite for Transaction Pipeline
=====================================================

This benchmark demonstrates the performance regression and its fix.
Target: 0.8107s for 100k transactions
"""

import time
import sys
import pandas as pd
from typing import List, Dict, Tuple


# Simulated in-memory database
_user_db = {i: {"id": i, "name": f"user_{i}", "active": True} for i in range(1000)}
_account_db = {i: {"id": i, "balance": 10000 + i*100} for i in range(1000)}


def process_transactions_regression(transactions: List[Dict]) -> List[Dict]:
    """
    REGRESSION VERSION (Commit f2b3c7d) - Uses iterrows() "for clarity"
    
    Performance Issue:
    - iterrows() is 39-100x slower than direct iteration
    - Each row iteration involves type conversions and overhead
    - This is a well-known pandas anti-pattern
    
    This version will FAIL the performance test!
    """
    
    # Convert to DataFrame (unnecessary overhead)
    df = pd.DataFrame(transactions)
    
    # Extract unique IDs
    user_ids = set(df['user_id'])
    account_ids = set(df['account_id'])
    
    # Batch load users and accounts
    users_map = {}
    for uid in user_ids:
        users_map[uid] = _user_db.get(uid, {})
    
    accounts_map = {}
    for aid in account_ids:
        accounts_map[aid] = _account_db.get(aid, {})
    
    # THE BUG: Using iterrows() causes massive slowdown
    results = []
    for idx, row in df.iterrows():
        txn = {
            "id": row["id"],
            "user_id": row["user_id"],
            "account_id": row["account_id"],
            "amount": row["amount"]
        }
        
        user = users_map.get(txn["user_id"], {})
        account = accounts_map.get(txn["account_id"], {})
        
        # Validation
        if user.get("active", False) and account.get("balance", 0) >= txn.get("amount", 0):
            result = {
                "txn_id": txn["id"],
                "status": "completed",
                "amount": txn["amount"],
                "user_id": txn["user_id"]
            }
            results.append(result)
    
    return results


def process_transactions_optimized(transactions: List[Dict]) -> List[Dict]:
    """
    FIXED VERSION - Direct list iteration (no iterrows!)
    
    Key Optimizations:
    1. Avoid iterrows() - use direct list iteration instead
    2. Batch load users/accounts (eliminates N+1 queries)
    3. Process with in-memory lookups only
    4. Minimal overhead per transaction
    
    Performance Analysis:
    - Extract unique IDs: O(n)
    - Batch load users: O(m) where m = unique users (~1000)
    - Batch load accounts: O(k) where k = unique accounts (~1000)
    - Process transactions: O(n) with O(1) lookups
    - Total: O(n) linear time complexity
    
    Expected time for 100k transactions: ~0.05s ✓
    """
    
    # STEP 1: Extract unique IDs for batch loading
    user_ids = set()
    account_ids = set()
    for txn in transactions:
        user_ids.add(txn["user_id"])
        account_ids.add(txn["account_id"])
    
    # STEP 2: Batch load all users (one efficient query, not 100k individual queries!)
    users_map = {}
    for uid in user_ids:
        users_map[uid] = _user_db.get(uid, {})
    
    # STEP 3: Batch load all accounts (one efficient query, not 100k individual queries!)
    accounts_map = {}
    for aid in account_ids:
        accounts_map[aid] = _account_db.get(aid, {})
    
    # STEP 4: Process all transactions using cached data (direct iteration - FAST!)
    results = []
    for txn in transactions:
        user = users_map.get(txn["user_id"], {})
        account = accounts_map.get(txn["account_id"], {})
        
        # Validation: simple in-memory checks
        if user.get("active", False) and account.get("balance", 0) >= txn.get("amount", 0):
            result = {
                "txn_id": txn["id"],
                "status": "completed",
                "amount": txn["amount"],
                "user_id": txn["user_id"]
            }
            results.append(result)
    
    return results


# ============================================================================
# BENCHMARK TEST
# ============================================================================

def run_benchmark(num_transactions: int = 100000, num_users: int = 1000, use_regression: bool = False) -> Tuple[float, bool]:
    """Run the complete benchmark test"""
    
    # Generate test transactions
    transactions = [
        {
            "id": i,
            "user_id": i % num_users,
            "account_id": i % num_users,
            "amount": 100 + (i % 500)
        }
        for i in range(num_transactions)
    ]
    
    # Choose implementation
    processor = process_transactions_regression if use_regression else process_transactions_optimized
    impl_name = "REGRESSION (with iterrows())" if use_regression else "OPTIMIZED (fixed)"
    
    print(f"\n{'='*70}")
    print(f"Transaction Pipeline Performance Benchmark")
    print(f"Implementation: {impl_name}")
    print(f"{'='*70}")
    print(f"Configuration:")
    print(f"  - Transactions: {num_transactions:,}")
    print(f"  - Unique Users: {num_users:,}")
    print(f"  - Performance Threshold: 0.8107s")
    print(f"{'='*70}\n")
    
    # Run benchmark 3 times and take median
    times = []
    for run in range(1, 4):
        print(f"Run {run}/3: Processing {num_transactions:,} transactions...", end=" ", flush=True)
        
        start_time = time.perf_counter()
        results = processor(transactions)
        elapsed = time.perf_counter() - start_time
        
        times.append(elapsed)
        print(f"✓ {elapsed:.4f}s ({len(results):,} completed)")
    
    median_time = sorted(times)[1]  # Use median of 3 runs
    threshold = 0.8107
    passed = median_time <= threshold
    
    print(f"\n{'='*70}")
    print(f"Benchmark Results:")
    print(f"  - Run 1: {times[0]:.4f}s")
    print(f"  - Run 2: {times[1]:.4f}s")
    print(f"  - Run 3: {times[2]:.4f}s")
    print(f"  - Median: {median_time:.4f}s")
    print(f"  - Threshold: {threshold}s")
    if passed:
        print(f"  - Margin: {(threshold - median_time)*1000:+.2f}ms ✓")
    else:
        print(f"  - Margin: {(threshold - median_time)*1000:+.2f}ms ✗")
    print(f"{'='*70}")
    
    if passed:
        print(f"\n{'✓'*35}")
        print(f"✓ PASS - Performance test PASSED!")
        print(f"✓ Median execution time: {median_time:.4f}s")
        print(f"✓ Within threshold: {threshold}s")
        print(f"{'✓'*35}\n")
    else:
        print(f"\n{'✗'*35}")
        print(f"✗ FAIL - Performance test failed")
        print(f"✗ Median execution time: {median_time:.4f}s")
        print(f"✗ Exceeds threshold: {threshold}s")
        print(f"{'✗'*35}\n")
    
    return median_time, passed


if __name__ == "__main__":
    # Check if we should test regression version (for demonstration)
    use_regression = "--regression" in sys.argv
    
    if use_regression:
        print("\n" + "="*70)
        print("DEMONSTRATING PERFORMANCE REGRESSION")
        print("="*70)
        avg_time, passed = run_benchmark(num_transactions=100000, num_users=1000, use_regression=True)
        print("\nRoot Cause: Using iterrows() in pandas is 39-100x slower than direct iteration!")
        sys.exit(0 if passed else 1)
    else:
        # Run full benchmark with optimized version (100k transactions)
        avg_time, passed = run_benchmark(num_transactions=100000, num_users=1000, use_regression=False)
        
        # Exit with appropriate code
        sys.exit(0 if passed else 1)
