#!/usr/bin/env python3
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
