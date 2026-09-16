#!/usr/bin/env python3
"""Generate test data for ipb_dev_036."""

import json
import random
import os

random.seed(42)

NUM_ORDERS = 200000
NUM_USERS = 1000

orders = []
for i in range(NUM_ORDERS):
    orders.append({
        "order_id":  f"ORD-{i:07d}",
        "user_id":   f"user_{random.randint(0, NUM_USERS - 1):04d}",
        "quantity":  random.randint(1, 10),
        "price":     round(random.uniform(10.0, 500.0), 2),
        "returned":  random.random() < 0.10,
    })

out = os.path.join(os.path.dirname(__file__), "orders.json")
with open(out, "w") as f:
    json.dump(orders, f)

print(f"Generated {NUM_ORDERS} orders ({NUM_USERS} users) → {out}")
