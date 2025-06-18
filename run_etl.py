#!/usr/bin/env python3
"""Main ETL runner"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.etl.simple_loader import test_load_openweather, check_data

print("🚀 Running ETL Pipeline")
print("=" * 50)

# Run the loader
test_load_openweather()

# Show summary
check_data()

print("\n✅ ETL run complete!")
