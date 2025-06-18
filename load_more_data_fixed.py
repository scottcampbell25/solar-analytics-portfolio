#!/usr/bin/env python3
"""Load more data and create mart table - fixed version"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

print("📊 Creating mart.pv_system_hourly table...")
print("=" * 60)

try:
    # Create database connection
    engine = create_engine(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics")
    
    # Check current data
    current_stats = pd.read_sql("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT site_id) as sites,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest
        FROM api_ingest.nrel_pvdaq
        WHERE timestamp IS NOT NULL
    """, engine)
    
    print("\n📈 Current Database Status:")
    print(f"   Total records: {current_stats['total_records'][0]}")
    print(f"   Sites: {current_stats['sites'][0]}")
    print(f"   Date range: {current_stats['earliest'][0]} to {current_stats['latest'][0]}")
    
    # Create mart table with proper SQL execution
    with engine.connect() as conn:
        # Drop existing table
        conn.execute(text("DROP TABLE IF EXISTS mart.pv_system_hourly"))
        conn.commit()
        
        # Create new table
        create_table_sql = text("""
            CREATE TABLE mart.pv_system_hourly AS
            SELECT 
                site_id,
                DATE_TRUNC('hour', timestamp) as hour,
                AVG(ac_power) as avg_ac_power,
                MAX(ac_power) as max_ac_power,
                MIN(ac_power) as min_ac_power,
                AVG(dc_power) as avg_dc_power,
                AVG(poa_irradiance) as avg_poa_irradiance,
                AVG(ambient_temp) as avg_ambient_temp,
                COUNT(*) as sample_count,
                EXTRACT(HOUR FROM DATE_TRUNC('hour', timestamp)) as hour_of_day,
                EXTRACT(DOW FROM DATE_TRUNC('hour', timestamp)) as day_of_week,
                EXTRACT(MONTH FROM DATE_TRUNC('hour', timestamp)) as month
            FROM api_ingest.nrel_pvdaq
            WHERE timestamp IS NOT NULL
                AND ac_power IS NOT NULL
            GROUP BY site_id, DATE_TRUNC('hour', timestamp)
        """)
        
        conn.execute(create_table_sql)
        conn.commit()
        
        # Create index
        conn.execute(text("CREATE INDEX idx_pv_hourly_site_hour ON mart.pv_system_hourly(site_id, hour)"))
        conn.commit()
        
        print("\n✅ Created mart.pv_system_hourly table")
    
    # Verify the mart table
    mart_stats = pd.read_sql("""
        SELECT 
            COUNT(*) as total_hours,
            COUNT(DISTINCT site_id) as sites,
            AVG(avg_ac_power) as overall_avg_power,
            MAX(max_ac_power) as peak_power,
            AVG(sample_count) as avg_samples_per_hour
        FROM mart.pv_system_hourly
    """, engine)
    
    print("\n📊 Mart Table Statistics:")
    print(f"   Hourly records: {mart_stats['total_hours'][0]}")
    print(f"   Unique sites: {mart_stats['sites'][0]}")
    print(f"   Average power: {mart_stats['overall_avg_power'][0]:.0f} W")
    print(f"   Peak power: {mart_stats['peak_power'][0]:.0f} W")
    print(f"   Samples per hour: {mart_stats['avg_samples_per_hour'][0]:.1f}")
    
    # Show sample data
    sample_data = pd.read_sql("""
        SELECT 
            hour,
            hour_of_day,
            avg_ac_power,
            avg_poa_irradiance
        FROM mart.pv_system_hourly
        WHERE hour_of_day BETWEEN 10 AND 14
        ORDER BY hour
        LIMIT 5
    """, engine)
    
    print("\n📋 Sample Peak Hours Data:")
    print(sample_data.to_string(index=False))
    
    # Create additional analysis table
    print("\n📊 Creating performance analysis view...")
    
    with engine.connect() as conn:
        # Create performance metrics view
        conn.execute(text("""
            CREATE OR REPLACE VIEW mart.pv_performance_metrics AS
            SELECT 
                site_id,
                hour_of_day,
                AVG(avg_ac_power) as typical_power,
                AVG(avg_poa_irradiance) as typical_irradiance,
                AVG(CASE WHEN avg_poa_irradiance > 0 
                    THEN avg_ac_power / avg_poa_irradiance 
                    ELSE 0 END) as efficiency,
                COUNT(*) as data_points
            FROM mart.pv_system_hourly
            GROUP BY site_id, hour_of_day
            ORDER BY site_id, hour_of_day
        """))
        conn.commit()
        
    print("✅ Created performance metrics view")
    
    # Show efficiency by hour
    efficiency_data = pd.read_sql("""
        SELECT 
            hour_of_day,
            AVG(typical_power) as avg_power,
            AVG(efficiency) as avg_efficiency
        FROM mart.pv_performance_metrics
        WHERE hour_of_day BETWEEN 6 AND 18
        GROUP BY hour_of_day
        ORDER BY hour_of_day
    """, engine)
    
    print("\n⚡ System Efficiency by Hour:")
    for _, row in efficiency_data.iterrows():
        hour = int(row['hour_of_day'])
        power = row['avg_power']
        eff = row['avg_efficiency']
        print(f"   {hour:02d}:00 - Power: {power:6.0f}W, Efficiency: {eff:.3f}")
    
    print("\n✅ Data enrichment complete!")
    print("\n🎯 Next steps:")
    print("1. Update visualizations with new data: python visualize_data_v2.py")
    print("2. Re-run metrics calculation: python calculate_metrics.py")
    print("3. Push updates to GitHub")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
