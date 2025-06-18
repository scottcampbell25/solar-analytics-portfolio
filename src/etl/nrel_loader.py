#!/usr/bin/env python3
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
                        lines = data_resp.text.split('\n')
                        
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
