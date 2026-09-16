"""
Transaction Processing Pipeline - SLOW VERSION (Before Optimization)
=====================================================================

Performance Issues:
1. N+1 query problem - queries user for every transaction
2. No batch processing - individual database commits
3. No caching - repeated lookups
4. Synchronous I/O - blocking audit logs
5. Sequential processing - no parallelization
"""

import time
from typing import List, Dict, Any


# Simulated database queries (slow, one-by-one)
_user_db = {i: {"id": i, "name": f"user_{i}", "active": True} for i in range(1000)}
_account_db = {i: {"id": i, "balance": 10000 + i*100, "user_id": i % 1000} for i in range(1000)}

_query_count = 0
_audit_logs = []


def query_user_by_id(user_id: int) -> Dict[str, Any]:
    """Simulates a slow database query - called for EVERY transaction (N+1 problem!)"""
    global _query_count
    _query_count += 1
    
    # Simulate network latency and database I/O
    time.sleep(0.00008)  # 80 microseconds per query
    
    return _user_db.get(user_id, {})


def fetch_account_balance(account_id: int) -> Dict[str, Any]:
    """Simulates repeated account lookups with no caching"""
    # Simulate database I/O
    time.sleep(0.000034)  # 34 microseconds per lookup
    
    return _account_db.get(account_id, {})


def validate_transaction(txn: Dict, user: Dict, account: Dict) -> bool:
    """Validates transaction sequentially"""
    time.sleep(0.0000056)  # Small validation overhead
    return user.get("active", False) and account.get("balance", 0) > txn.get("amount", 0)


def process_transaction(txn: Dict) -> Dict:
    """Processes a single transaction with synchronous database write"""
    # Simulate database write
    time.sleep(0.000041)  # 41 microseconds per write
    
    return {
        "txn_id": txn["id"],
        "status": "completed",
        "amount": txn["amount"],
        "timestamp": time.time()
    }


def audit_log_write(result: Dict) -> None:
    """Writes to audit log synchronously - blocking operation"""
    global _audit_logs
    time.sleep(0.0000014)  # 1.4 microseconds per log write (still adds up)
    _audit_logs.append(result)


def process_transactions_slow(transactions: List[Dict]) -> List[Dict]:
    """
    SLOW IMPLEMENTATION - The original performance problem
    
    Issues:
    - N+1 queries: calls query_user_by_id() for EVERY transaction
    - No caching: fetches same user/account data repeatedly
    - Sequential: processes one transaction at a time
    - Synchronous I/O: waits for audit logs
    """
    results = []
    
    for txn in transactions:
        # PROBLEM #1: N+1 Query - query user for every single transaction!
        user = query_user_by_id(txn["user_id"])
        
        # PROBLEM #2: No caching - fetch account every time
        account = fetch_account_balance(txn["account_id"])
        
        # Validate
        if validate_transaction(txn, user, account):
            result = process_transaction(txn)
            # PROBLEM #3: Synchronous blocking I/O
            audit_log_write(result)
            results.append(result)
    
    return results


if __name__ == "__main__":
    # Test with small dataset
    test_txns = [
        {"id": i, "user_id": i % 1000, "account_id": i % 1000, "amount": 100}
        for i in range(1000)
    ]
    
    start = time.time()
    results = process_transactions_slow(test_txns)
    elapsed = time.time() - start
    
    print(f"Processed {len(results)} transactions in {elapsed:.4f}s")
    print(f"Database queries made: {_query_count} (expected: ~1000, actual: {_query_count})")
