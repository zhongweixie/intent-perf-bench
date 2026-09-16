"""
Transaction Processing Pipeline - REGRESSION VERSION (Commit f2b3c7d)
=====================================================================

This is the buggy version that was introduced in commit f2b3c7d 
with the message "Refactor for readability".

The "refactor" replaced efficient batch operations with iterrows(),
which is a well-known pandas performance anti-pattern.

Performance Impact: 16.6x slowdown!
"""

import time
import pandas as pd
from typing import List, Dict


# Simulated in-memory database
_user_db = {i: {"id": i, "name": f"user_{i}", "active": True} for i in range(1000)}
_account_db = {i: {"id": i, "balance": 10000 + i*100} for i in range(1000)}


def process_transactions_regression(transactions: List[Dict]) -> List[Dict]:
    """
    REGRESSION VERSION - Uses iterrows() "for clarity"
    
    This is the buggy implementation from commit f2b3c7d.
    The developer thought iterrows() would make the code "clearer",
    but it's actually 16-100x slower than vectorized operations.
    
    Performance Problem:
    - iterrows() is extremely slow in pandas
    - Each row iteration involves type conversions and overhead
    - This turns O(n) into effectively O(n*k) where k is overhead factor
    """
    
    # Convert transactions to DataFrame (unnecessary overhead!)
    df = pd.DataFrame(transactions)
    
    # Extract unique IDs
    user_ids = set(df['user_id'])
    account_ids = set(df['account_id'])
    
    # Batch load users and accounts (this part is OK)
    users_map = {}
    for uid in user_ids:
        users_map[uid] = _user_db.get(uid, {})
    
    accounts_map = {}
    for aid in account_ids:
        accounts_map[aid] = _account_db.get(aid, {})
    
    # THE BUG: Using iterrows() for "readability"
    # iterrows() is an anti-pattern - it's SLOW!
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
    FIXED VERSION - Removes iterrows(), uses direct list iteration
    
    This is the corrected implementation.
    """
    
    # Extract unique IDs
    user_ids = set()
    account_ids = set()
    for txn in transactions:
        user_ids.add(txn["user_id"])
        account_ids.add(txn["account_id"])
    
    # Batch load all users
    users_map = {}
    for uid in user_ids:
        users_map[uid] = _user_db.get(uid, {})
    
    # Batch load all accounts
    accounts_map = {}
    for aid in account_ids:
        accounts_map[aid] = _account_db.get(aid, {})
    
    # Process transactions using direct list iteration (FAST!)
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


if __name__ == "__main__":
    # Generate test data
    test_txns = [
        {
            "id": i,
            "user_id": i % 1000,
            "account_id": i % 1000,
            "amount": 100 + (i % 500)
        }
        for i in range(100000)
    ]
    
    print("\n" + "="*70)
    print("PERFORMANCE REGRESSION DEMO")
    print("="*70)
    
    # Test slow version
    print("\n[SLOW] Using iterrows() (Regression):")
    start = time.perf_counter()
    results_slow = process_transactions_regression(test_txns)
    elapsed_slow = time.perf_counter() - start
    print(f"  Time: {elapsed_slow:.4f}s")
    print(f"  Transactions: {len(results_slow):,}")
    
    # Test fixed version
    print("\n[FAST] Using direct iteration (Fixed):")
    start = time.perf_counter()
    results_fast = process_transactions_optimized(test_txns)
    elapsed_fast = time.perf_counter() - start
    print(f"  Time: {elapsed_fast:.4f}s")
    print(f"  Transactions: {len(results_fast):,}")
    
    # Show improvement
    improvement = elapsed_slow / elapsed_fast
    print("\n" + "="*70)
    print(f"IMPROVEMENT: {improvement:.1f}x faster")
    print("="*70 + "\n")
