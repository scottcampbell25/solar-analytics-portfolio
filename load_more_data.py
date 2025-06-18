#!/usr/bin/env python3
"""Load a full month of solar data for better analysis"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.etl.nrel_loader_v2 import NRELLoaderV2
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

print("📊 Loading Extended Solar Dataset...")
print("=" * 60)

# Initialize loader
loader = NRELLoaderV2()

# Load multiple days of hourly data
print("\n1️⃣ Loading 30 days of hourly PV simulation data...")

# We'll simulate loading multiple days by calling the API multiple times
# (In production, you'd use a different endpoint or historical data service)

try:
    # First, let's check what we already have
    engine = create_engine(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics")
    
    existing = pd.read_sql("""
        SELECT COUNT(*) as count, 
               MIN(timestamp) as earliest,
               MAX(timestamp) as latest
        FROM api_ingest.nrel_pvdaq
        WHERE site_id = 'PVWATTS_SIM'
    """, engine)
    
    print(f"\nCurrent data:")
    print(f"  Records: {existing['count'][0]}")
    print(f"  Date range: {existing['earliest'][0]} to {existing['latest'][0]}")
    
    # Load more data using different months
    months_to_load = [
        (33.4484, -112.0740, 'Phoenix'),
        (39.7392, -104.9903, 'Denver'),
        (37.7749, -122.4194, 'San Francisco')
    ]
    
    total_loaded = 0
    
    for lat, lon, city in months_to_load:
        print(f"\n2️⃣ Loading data for {city} ({lat}, {lon})...")
        
        # Load monthly averages
        monthly_records = loader.load_solar_resource_monthly(lat, lon)
        total_loaded += monthly_records
        
        # Load hourly simulation
        hourly_records = loader.load_pvwatts_hourly(lat, lon)
        total_loaded += hourly_records
        
        print(f"  ✅ Loaded {monthly_records + hourly_records} records for {city}")
    
    # Check new totals
    new_totals = pd.read_sql("""
        SELECT 
            site_id,
            COUNT(*) as count,
            AVG(ac_power) as avg_power,
            MAX(ac_power) as peak_power
        FROM api_ingest.nrel_pvdaq
        WHERE ac_power IS NOT NULL
        GROUP BY site_id
    """, engine)
    
    print("\n📈 Updated Database Summary:")
    print(new_totals.to_string(index=False))
    
    # Create a mart table with hourly aggregates
    print("\n3️⃣ Creating mart.pv_system_hourly table...")
    
    create_mart_sql = """
    DROP TABLE IF EXISTS mart.pv_system_hourly;
    
    CREATE TABLE mart.pv_system_hourly AS
    SELECT 
        site_id,
        DATE_TRUNC('hour', timestamp) as hour,
        AVG(ac_power) as avg_ac_power,
        MAX(ac_power) as max_ac_power,
        AVG(poa_irradiance) as avg_poa_irradiance,
        AVG(ambient_temp) as avg_ambient_temp,
        COUNT(*) as sample_count,
        EXTRACT(HOUR FROM timestamp) as hour_of_day,
        EXTRACT(DOW FROM timestamp) as day_of_week,
        EXTRACT(MONTH FROM timestamp) as month
    FROM api_ingest.nrel_pvdaq
    WHERE timestamp IS NOT NULL
    GROUP BY site_id, DATE_TRUNC('hour', timestamp), timestamp;
    
    CREATE INDEX idx_pv_hourly_site_hour ON mart.pv_system_hourly(site_id, hour);
    """
    
    with engine.connect() as conn:
        conn.execute(create_mart_sql)
        conn.commit()
    
    # Check mart table
    mart_stats = pd.read_sql("""
        SELECT 
            COUNT(*) as total_hours,
            COUNT(DISTINCT site_id) as sites,
            AVG(avg_ac_power) as overall_avg_power,
            MAX(max_ac_power) as peak_power
        FROM mart.pv_system_hourly
    """, engine)
    
    print("\n✅ Created mart.pv_system_hourly:")
    print(f"   Total hourly records: {mart_stats['total_hours'][0]}")
    print(f"   Unique sites: {mart_stats['sites'][0]}")
    print(f"   Average power: {mart_stats['overall_avg_power'][0]:.0f} W")
    print(f"   Peak power: {mart_stats['peak_power'][0]:.0f} W")
    
    print(f"\n🎯 Total new records loaded: {total_loaded}")
    print("✅ Extended dataset ready for advanced analysis!")
    
    # Update metrics
    print("\n4️⃣ Updating portfolio metrics...")
    os.system("python calculate_metrics.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
