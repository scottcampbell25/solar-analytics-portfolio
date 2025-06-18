#!/usr/bin/env python3
"""Create the full ETL pipeline files"""

import os

print("Creating full ETL pipeline...")

# 1. Create database tables setup
db_tables_content = '''#!/usr/bin/env python3
"""Create all database tables for solar analytics"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def create_all_tables():
    """Create all tables needed for the project"""
    
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # NREL PVDAQ table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_ingest.nrel_pvdaq (
                id SERIAL PRIMARY KEY,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                site_id VARCHAR(50),
                timestamp TIMESTAMP,
                dc_power FLOAT,
                ac_power FLOAT,
                poa_irradiance FLOAT,
                ghi FLOAT,
                dni FLOAT,
                dhi FLOAT,
                module_temp FLOAT,
                ambient_temp FLOAT,
                wind_speed FLOAT,
                raw_json JSONB
            );
        """))
        print("✅ Created nrel_pvdaq table")
        
        # NOAA Weather table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_ingest.noaa_weather (
                id SERIAL PRIMARY KEY,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                station_id VARCHAR(50),
                forecast_time TIMESTAMP,
                valid_time TIMESTAMP,
                temperature FLOAT,
                wind_speed FLOAT,
                wind_direction FLOAT,
                cloud_cover INTEGER,
                precipitation_prob FLOAT,
                raw_json JSONB
            );
        """))
        print("✅ Created noaa_weather table")
        
        # Tomorrow.io Weather table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_ingest.tomorrow_weather (
                id SERIAL PRIMARY KEY,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                location_lat FLOAT,
                location_lon FLOAT,
                forecast_time TIMESTAMP,
                valid_time TIMESTAMP,
                temperature FLOAT,
                solar_ghi FLOAT,
                solar_dni FLOAT,
                cloud_cover FLOAT,
                precipitation_intensity FLOAT,
                raw_json JSONB
            );
        """))
        print("✅ Created tomorrow_weather table")
        
        # Features table for analysis
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mart.solar_forecast_features (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                site_id VARCHAR(50),
                timestamp TIMESTAMP,
                hour INTEGER,
                day_of_year INTEGER,
                actual_power FLOAT,
                actual_irradiance FLOAT,
                forecast_temperature FLOAT,
                forecast_cloud_cover FLOAT,
                forecast_ghi FLOAT,
                temperature_error FLOAT,
                irradiance_error FLOAT
            );
        """))
        print("✅ Created solar_forecast_features table")
        
        conn.commit()

if __name__ == "__main__":
    print("Creating database tables...")
    create_all_tables()
    print("✅ All tables created!")
'''

with open('create_tables.py', 'w') as f:
    f.write(db_tables_content)
print("✅ Created create_tables.py")

# 2. Create NREL loader (simplified version)
nrel_loader_content = '''#!/usr/bin/env python3
"""NREL Solar Data Loader - Using public NSRDB data"""

import os
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import requests
import json

load_dotenv()

class NRELLoader:
    def __init__(self):
        self.api_key = os.getenv('NREL_API_KEY')
        self.engine = self._get_db_engine()
    
    def _get_db_engine(self):
        db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
        return create_engine(db_url)
    
    def load_solar_resource_data(self, lat=33.4484, lon=-112.0740, year=2022):
        """Load solar resource data from NREL NSRDB"""
        print(f"Loading NREL solar data for {lat}, {lon}...")
        
        # NSRDB API endpoint
        url = 'https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-5min-download.json'
        
        params = {
            'api_key': self.api_key,
            'lat': lat,
            'lon': lon,
            'year': year,
            'interval': 60,  # 60-minute intervals
            'attributes': 'ghi,dni,dhi,air_temperature,wind_speed',
            'name': 'Test+Site',
            'email': 'test@example.com'
        }
        
        try:
            # This returns a download URL
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                
                # Get the download URL
                if 'outputs' in data and 'downloadUrl' in data['outputs']:
                    download_url = data['outputs']['downloadUrl']
                    
                    # Download the actual data
                    print("Downloading solar data...")
                    data_resp = requests.get(download_url)
                    
                    if data_resp.status_code == 200:
                        # Parse CSV data
                        lines = data_resp.text.split('\\n')
                        
                        # Skip metadata rows (first 2 rows)
                        data_lines = [line for line in lines[2:] if line.strip()]
                        
                        # Create DataFrame
                        if data_lines:
                            # Parse header
                            header = data_lines[0].split(',')
                            
                            # Sample just first 24 hours for testing
                            records = []
                            for line in data_lines[1:25]:  # Just first day
                                values = line.split(',')
                                if len(values) >= 8:
                                    record = {
                                        'site_id': 'NREL_TEST',
                                        'timestamp': pd.to_datetime(f"{values[0]}-{values[1]:0>2}-{values[2]:0>2} {values[3]:0>2}:{values[4]:0>2}"),
                                        'ghi': float(values[5]) if values[5] else 0,
                                        'dni': float(values[6]) if values[6] else 0,
                                        'dhi': float(values[7]) if values[7] else 0,
                                        'ambient_temp': float(values[8]) if len(values) > 8 and values[8] else None,
                                        'wind_speed': float(values[9]) if len(values) > 9 and values[9] else None,
                                        'raw_json': json.dumps({'lat': lat, 'lon': lon})
                                    }
                                    records.append(record)
                            
                            if records:
                                df = pd.DataFrame(records)
                                df.to_sql('nrel_pvdaq', self.engine, schema='api_ingest', 
                                         if_exists='append', index=False)
                                print(f"✅ Loaded {len(records)} NREL records")
                                return len(records)
                
                print(f"❌ No download URL in response")
                return 0
            else:
                print(f"❌ NREL API error: {resp.status_code}")
                return 0
                
        except Exception as e:
            print(f"❌ Error loading NREL data: {e}")
            return 0

if __name__ == "__main__":
    loader = NRELLoader()
    loader.load_solar_resource_data()
'''

with open('src/etl/nrel_loader.py', 'w') as f:
    f.write(nrel_loader_content)
print("✅ Created src/etl/nrel_loader.py")

# 3. Create full pipeline runner
pipeline_content = '''#!/usr/bin/env python3
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
    print("\\n📊 Loading current weather...")
    if test_load_openweather():
        results['openweather'] = 'success'
    else:
        results['openweather'] = 'failed'
    
    # 2. Load NREL solar data
    print("\\n📊 Loading NREL solar data...")
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
    print("\\n📈 Pipeline Summary:")
    for source, status in results.items():
        print(f"   {source}: {status}")
    
    # 4. Check database
    check_data()
    
    print(f"\\n✅ Pipeline completed at: {datetime.now()}")

if __name__ == "__main__":
    run_pipeline()
'''

with open('run_pipeline.py', 'w') as f:
    f.write(pipeline_content)
print("✅ Created run_pipeline.py")

print("\n✅ Full ETL pipeline created!")
print("\nNext steps:")
print("1. python create_tables.py    # Create all database tables")
print("2. python run_pipeline.py     # Run the full ETL pipeline")
