#!/usr/bin/env python3
"""Run the complete ETL pipeline"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.etl.simple_loader_fixed import test_load_openweather, check_data
from src.etl.nrel_loader import NRELLoader

def run_pipeline():
    """Run all ETL processes"""
    print(f"🚀 Solar Analytics ETL Pipeline")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    results = {}
    
    # 1. Load weather data
    print("\n📊 Loading current weather...")
    if test_load_openweather():
        results['openweather'] = 'success'
    else:
        results['openweather'] = 'failed'
    
    # 2. Load NREL solar data
    print("\n📊 Loading NREL solar data...")
    try:
        nrel = NRELLoader()
        records = nrel.load_solar_resource_data()
        if records > 0:
            results['nrel'] = f'success ({records} records)'
        else:
            results['nrel'] = 'no data'
    except Exception as e:
        results['nrel'] = f'error: {e}'
    
    # 3. Show summary
    print("\n📈 Pipeline Summary:")
    for source, status in results.items():
        print(f"   {source}: {status}")
    
    # 4. Check database
    check_data()
    
    print(f"\n✅ Pipeline completed at: {datetime.now()}")

if __name__ == "__main__":
    run_pipeline()
