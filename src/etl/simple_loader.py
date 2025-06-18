#!/usr/bin/env python3
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
        
        print(f"\n📊 Database status:")
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
