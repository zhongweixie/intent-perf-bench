# Transaction Data

The production pipeline writes `data/transactions.parquet` from the
data-warehouse ETL job (not committed to this repo — too large).

Schema
──────
| Column         | Type    | Description                       |
|----------------|---------|-----------------------------------|
| transaction_id | int64   | Unique transaction identifier     |
| store_id       | int32   | Store location (0–999)            |
| amount         | float64 | Transaction amount in USD         |
| units          | int16   | Number of units sold              |
| returned       | bool    | True if the order was returned    |

Production stats: ~3 000 000 rows/day, ~1 000 distinct stores.

Dev / CI mode: `load_transactions()` generates deterministic synthetic data
in memory (no file needed).  Pass `--parquet data/transactions.parquet`
to use the real file if available locally.
