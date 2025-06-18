#!/usr/bin/env python3
"""Complete ETL Pipeline with all working components"""

import sys
import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.etl.simple_loader_fixed import test_load_openweather
from src.etl.nrel_loader_v2 import NRELLoaderV2
from src.etl.tomorrow_loader_v3 import TomorrowLoaderV3

load_dotenv()

def get_db_engine():
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
    return create_engine(db_url)

def create_portfolio_summary():
    """Create a professional summary of the portfolio project"""
    engine = get_db_engine()
    
    print("\n" + "="*70)
    print("🌟 SOLAR ANALYTICS PORTFOLIO - DATA PIPELINE SUMMARY 🌟")
    print("="*70)
    
    # Count all records
    tables = {
        'api_ingest.weather_test': 'Real-time Weather',
        'api_ingest.nrel_pvdaq': 'Solar Resource & PV Simulation',
        'api_ingest.tomorrow_weather': 'Weather Forecast'
    }
    
    total_records = 0
    for table, name in tables.items():
        try:
            count = pd.read_sql(f"SELECT COUNT(*) as n FROM {table}", engine)['n'][0]
            total_records += count
            print(f"✅ {name:.<40} {count:,} records")
        except:
            print(f"⏳ {name:.<40} pending")
    
    print(f"\n📊 TOTAL RECORDS IN DATABASE: {total_records:,}")
    
    # Show data freshness
    print("\n🕐 DATA FRESHNESS:")
    try:
        freshness = pd.read_sql("""
            SELECT 
                'Weather' as source,
                MAX(timestamp) as latest
            FROM api_ingest.weather_test
            UNION ALL
            SELECT 
                'Solar Forecast' as source,
                MAX(valid_time) as latest
            FROM api_ingest.tomorrow_weather
            WHERE valid_time IS NOT NULL
        """, engine)
        
        for _, row in freshness.iterrows():
            if pd.notna(row['latest']):
                age = (datetime.now() - pd.to_datetime(row['latest'])).total_seconds() / 60
                print(f"   {row['source']}: {row['latest']} ({age:.0f} minutes ago)")
    except:
        pass
    
    print("\n🎯 PROJECT CAPABILITIES DEMONSTRATED:")
    print("   ✅ Multi-source API integration (NREL, OpenWeather, Tomorrow.io)")
    print("   ✅ PostgreSQL data warehouse with proper schema design")
    print("   ✅ Automated ETL pipeline with error handling")
    print("   ✅ Time-series data management")
    print("   ✅ Solar energy domain knowledge")
    print("   ✅ Production-ready code structure")
    
    print("\n💼 BUSINESS VALUE:")
    print("   • Enables accurate solar power forecasting")
    print("   • Reduces grid integration costs")
    print("   • Improves renewable energy reliability")
    print("   • Supports data-driven O&M decisions")

def run_complete_pipeline():
    """Run all ETL processes"""
    print(f"🚀 Starting Solar Analytics ETL Pipeline")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    results = {}
    
    # 1. Current Weather
    print("\n1️⃣ Loading current weather data...")
    try:
        test_load_openweather()
        results['OpenWeather'] = 'SUCCESS'
    except Exception as e:
        results['OpenWeather'] = f'ERROR: {str(e)[:30]}'
    
    # 2. NREL Solar Data (only if needed)
    print("\n2️⃣ Checking NREL solar data...")
    try:
        engine = get_db_engine()
        nrel_count = pd.read_sql("SELECT COUNT(*) as n FROM api_ingest.nrel_pvdaq", engine)['n'][0]
        
        if nrel_count < 60:  # Load if we have less than 60 records
            nrel = NRELLoaderV2()
            nrel.load_solar_resource_monthly()
            nrel.load_pvwatts_hourly()
            results['NREL'] = 'LOADED NEW DATA'
        else:
            results['NREL'] = f'SKIPPED ({nrel_count} records exist)'
    except Exception as e:
        results['NREL'] = f'ERROR: {str(e)[:30]}'
    
    # 3. Weather Forecast
    print("\n3️⃣ Loading weather forecast...")
    try:
        tomorrow = TomorrowLoaderV3()
        records = tomorrow.load_forecast()
        results['Tomorrow.io'] = f'SUCCESS ({records} hours)'
    except Exception as e:
        results['Tomorrow.io'] = f'ERROR: {str(e)[:30]}'
    
    # Show results
    print("\n" + "-" * 70)
    print("📋 PIPELINE EXECUTION RESULTS:")
    for source, status in results.items():
        icon = "✅" if "SUCCESS" in status or "SKIPPED" in status else "❌"
        print(f"   {icon} {source:.<30} {status}")
    
    # Show portfolio summary
    create_portfolio_summary()
    
    print("\n✨ Pipeline execution completed!")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    run_complete_pipeline()
