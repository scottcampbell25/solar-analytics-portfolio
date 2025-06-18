#!/usr/bin/env python3
"""Create all ETL files for the solar analytics project"""

import os

# Make sure directories exist
os.makedirs("src/etl", exist_ok=True)

print("Creating ETL files...")

# 1. Create __init__.py
init_content = '''"""ETL Package for Solar Analytics"""
'''

with open('src/etl/__init__.py', 'w') as f:
    f.write(init_content)
print("✅ Created src/etl/__init__.py")

# 2. Create test_apis.py
test_apis_content = '''#!/usr/bin/env python3
"""Test all API connections"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("Testing API connections...")

# Test NREL
print("\\n1. Testing NREL API...")
try:
    url = f"https://developer.nrel.gov/api/alt-fuel-stations/v1.json?limit=1&api_key={os.getenv('NREL_API_KEY')}"
    resp = requests.get(url, timeout=10)
    print(f"   NREL: {resp.status_code} - {'✅ OK' if resp.status_code == 200 else '❌ Failed'}")
    if resp.status_code != 200:
        print(f"   Response: {resp.text[:200]}")
except Exception as e:
    print(f"   NREL: ❌ Error - {e}")

# Test Tomorrow.io
print("\\n2. Testing Tomorrow.io API...")
try:
    url = "https://api.tomorrow.io/v4/weather/realtime"
    params = {
        'location': '33.4484,-112.0740',
        'apikey': os.getenv('TOMORROW_API_KEY')
    }
    resp = requests.get(url, params=params, timeout=10)
    print(f"   Tomorrow.io: {resp.status_code} - {'✅ OK' if resp.status_code == 200 else '❌ Failed'}")
    if resp.status_code != 200:
        print(f"   Response: {resp.text[:200]}")
except Exception as e:
    print(f"   Tomorrow.io: ❌ Error - {e}")

# Test OpenWeather
print("\\n3. Testing OpenWeather API...")
try:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': 33.4484,
        'lon': -112.0740,
        'appid': os.getenv('OPENWEATHER_API_KEY')
    }
    resp = requests.get(url, params=params, timeout=10)
    print(f"   OpenWeather: {resp.status_code} - {'✅ OK' if resp.status_code == 200 else '❌ Failed'}")
    if resp.status_code != 200:
        print(f"   Response: {resp.text[:200]}")
except Exception as e:
    print(f"   OpenWeather: ❌ Error - {e}")

# Test NOAA (no auth needed)
print("\\n4. Testing NOAA API...")
try:
    url = "https://api.weather.gov/points/33.4484,-112.0740"
    headers = {'User-Agent': 'SolarAnalytics/1.0'}
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"   NOAA: {resp.status_code} - {'✅ OK' if resp.status_code == 200 else '❌ Failed'}")
except Exception as e:
    print(f"   NOAA: ❌ Error - {e}")

print("\\n✅ API test complete!")
'''

with open('src/etl/test_apis.py', 'w') as f:
    f.write(test_apis_content)
print("✅ Created src/etl/test_apis.py")

# 3. Create simple_loader.py
simple_loader_content = '''#!/usr/bin/env python3
"""Simple data loader to test the pipeline"""

import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv
import requests

load_dotenv()

def get_db_engine():
    """Create database connection"""
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
    return create_engine(db_url)

def test_load_openweather():
    """Load current weather from OpenWeather"""
    print("Loading OpenWeather data...")
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': 33.4484,
        'lon': -112.0740,
        'appid': os.getenv('OPENWEATHER_API_KEY'),
        'units': 'metric'
    }
    
    try:
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            
            # Create a simple record
            record = {
                'timestamp': datetime.now(),
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'description': data['weather'][0]['description']
            }
            
            # Save to test table
            engine = get_db_engine()
            df = pd.DataFrame([record])
            
            # First create a test table if it doesn't exist
            with engine.connect() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS api_ingest.weather_test (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP,
                        temperature FLOAT,
                        humidity FLOAT,
                        wind_speed FLOAT,
                        description TEXT
                    );
                """)
                conn.commit()
            
            # Insert the data
            df.to_sql('weather_test', engine, schema='api_ingest', if_exists='append', index=False)
            print(f"✅ Saved weather data: {record['temperature']}°C, {record['description']}")
            
            return True
        else:
            print(f"❌ API error: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_data():
    """Check what data we have in the database"""
    try:
        engine = get_db_engine()
        
        # Check if we have data
        result = pd.read_sql("""
            SELECT COUNT(*) as count, 
                   MAX(timestamp) as latest,
                   AVG(temperature) as avg_temp
            FROM api_ingest.weather_test
        """, engine)
        
        print(f"\\n📊 Database status:")
        print(f"   Records: {result['count'][0]}")
        if result['count'][0] > 0:
            print(f"   Latest: {result['latest'][0]}")
            print(f"   Avg temp: {result['avg_temp'][0]:.1f}°C")
    except Exception as e:
        print(f"❌ Error checking data: {e}")

if __name__ == "__main__":
    print("🚀 Simple ETL Test")
    print("=" * 50)
    
    # Load some data
    if test_load_openweather():
        # Check what we have
        check_data()
'''

with open('src/etl/simple_loader.py', 'w') as f:
    f.write(simple_loader_content)
print("✅ Created src/etl/simple_loader.py")

# 4. Create run_etl.py
run_etl_content = '''#!/usr/bin/env python3
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

print("\\n✅ ETL run complete!")
'''

with open('run_etl.py', 'w') as f:
    f.write(run_etl_content)
print("✅ Created run_etl.py")

print("\n✅ All ETL files created!")
print("\nNext steps:")
print("1. python src/etl/test_apis.py   # Test your API connections")
print("2. python src/etl/simple_loader.py  # Test loading data")
print("3. python run_etl.py              # Run the full ETL")
