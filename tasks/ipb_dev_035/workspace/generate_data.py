#!/usr/bin/env python3
"""Generate test data for ipb_dev_035."""

import json
import random
import os

random.seed(42)

NUM_ORDERS = 50000

orders = []
for i in range(NUM_ORDERS):
    orders.append({
        "order_id": f"ORD-{i:06d}",
        "base_price": round(random.uniform(10.0, 500.0), 2),
        "quantity": random.randint(1, 20),
        "discount_rate": round(random.uniform(0.0, 0.30), 4),
        "tax_rate": round(random.uniform(0.05, 0.20), 4),
        "handling_fee": round(random.uniform(0.0, 15.0), 2),
    })

out = os.path.join(os.path.dirname(__file__), "orders.json")
with open(out, "w") as f:
    json.dump(orders, f)

print(f"Generated {NUM_ORDERS} orders → {out}")
