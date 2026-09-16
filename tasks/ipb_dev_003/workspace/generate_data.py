"""Generate sample transaction data for testing."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def generate_transactions(n_transactions=100_000, n_customers=1_000):
    """Generate synthetic transaction data."""
    np.random.seed(42)
    
    start_date = datetime(2024, 1, 1)
    
    data = {
        'transaction_id': range(n_transactions),
        'customer_id': np.random.randint(1, n_customers + 1, n_transactions),
        'timestamp': [start_date + timedelta(hours=np.random.randint(0, 720)) 
                      for _ in range(n_transactions)],
        'amount': np.random.exponential(50, n_transactions),
        'category': np.random.choice(['grocery', 'electronics', 'clothing', 'dining'], n_transactions),
        'store_id': np.random.randint(1, 51, n_transactions),
    }
    
    df = pd.DataFrame(data)
    df['amount'] = df['amount'].round(2)
    
    # Add some nulls (5%)
    null_mask = np.random.random(n_transactions) < 0.05
    df.loc[null_mask, 'category'] = None
    
    return df

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    
    print("Generating transaction data...")
    df = generate_transactions()
    
    output_path = "data/transactions.parquet"
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Generated {len(df)} transactions")
    print(f"✓ Saved to {output_path}")
    print(f"  Size: {Path(output_path).stat().st_size / 1024:.1f} KB")
