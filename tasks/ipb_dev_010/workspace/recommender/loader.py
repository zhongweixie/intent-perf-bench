"""Product & User Data Loader

Fetches product catalog and user preference data from remote API.
"""
import time
import numpy as np
import pandas as pd


class DataLoader:
    """Load product and user data from remote source."""

    def __init__(self, simulate_network: bool = True):
        self.simulate_network = simulate_network

    def load_data(self, n_users: int = 500, n_products: int = 200) -> tuple:
        """Load user preferences and product catalog. Simulates network I/O."""
        if self.simulate_network:
            # Simulate API call latency (product catalog + user preferences)
            time.sleep(0.69)

        np.random.seed(42)

        # Product catalog
        products = pd.DataFrame({
            'product_id': range(n_products),
            'category': np.random.choice(['electronics', 'clothing', 'books', 'food'], n_products),
            'price': np.random.uniform(10, 500, n_products),
            'rating': np.random.uniform(1, 5, n_products),
            'stock': np.random.randint(0, 100, n_products),
        })

        # User preferences
        users = pd.DataFrame({
            'user_id': range(n_users),
            'pref_electronics': np.random.uniform(0, 1, n_users),
            'pref_clothing': np.random.uniform(0, 1, n_users),
            'pref_books': np.random.uniform(0, 1, n_users),
            'pref_food': np.random.uniform(0, 1, n_users),
            'budget': np.random.uniform(20, 600, n_users),
        })

        return products, users
