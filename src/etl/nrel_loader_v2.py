#!/usr/bin/env python3
"""NREL Data Loader - Using simpler API endpoints"""

import os
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import requests
import json
import time

load_dotenv()

class NRELLoaderV2:
    def __init__(self):
        self.api_key = os.getenv('NREL_API_KEY')
        self.engine = self._get_db_engine()
    
    def _get_db_engine(self):
        db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
        return create_engine(db_url)
    
    def test_api(self):
        """Test NREL API with a simple request"""
        print("Testing NREL API connection...")
        
        # Test with solar resource data
        url = "https://developer.nrel.gov/api/solar/solar_resource/v1.json"
        params = {
            'api_key': self.api_key,
            'lat': 40,
            'lon': -105
        }
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            print(f"API Response: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print("✅ NREL API working!")
                print(f"Sample data: {list(data.keys())[:5]}")
                return True
            else:
                print(f"❌ Error: {resp.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def load_solar_resource_monthly(self, lat=33.4484, lon=-112.0740):
        """Load monthly average solar data"""
        print(f"Loading monthly solar averages for {lat}, {lon}...")
        
        url = "https://developer.nrel.gov/api/solar/solar_resource/v1.json"
        params = {
            'api_key': self.api_key,
            'lat': lat,
            'lon': lon
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                
                # Extract monthly averages
                if 'outputs' in data:
                    outputs = data['outputs']
                    avg_dni = outputs.get('avg_dni', {})
                    avg_ghi = outputs.get('avg_ghi', {})
                    
                    # Create records for each month
                    records = []
                    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                             'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                    
                    for i, month in enumerate(months, 1):
                        if 'monthly' in avg_dni and 'monthly' in avg_ghi:
                            record = {
                                'site_id': 'NREL_MONTHLY',
                                'timestamp': pd.to_datetime(f'2024-{i:02d}-15'),  # Middle of month
                                'ghi': avg_ghi['monthly'].get(month, 0),
                                'dni': avg_dni['monthly'].get(month, 0),
                                'dhi': 0,  # Not available in this endpoint
                                'ambient_temp': None,
                                'wind_speed': None,
                                'raw_json': json.dumps({'month': month, 'data': outputs})
                            }
                            records.append(record)
                    
                    if records:
                        df = pd.DataFrame(records)
                        df.to_sql('nrel_pvdaq', self.engine, schema='api_ingest', 
                                 if_exists='append', index=False)
                        print(f"✅ Loaded {len(records)} monthly records")
                        
                        # Show sample
                        print("\nSample data:")
                        for r in records[:3]:
                            print(f"  {r['timestamp'].strftime('%B')}: GHI={r['ghi']:.1f}, DNI={r['dni']:.1f}")
                        
                        return len(records)
                else:
                    print("❌ No outputs in response")
                    print(f"Response: {data}")
                    return 0
            else:
                print(f"❌ API error: {resp.status_code}")
                print(f"Response: {resp.text[:500]}")
                return 0
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0
    
    def load_pvwatts_hourly(self, lat=33.4484, lon=-112.0740):
        """Load hourly PV simulation data using PVWatts"""
        print(f"\nLoading PVWatts hourly data for {lat}, {lon}...")
        
        url = "https://developer.nrel.gov/api/pvwatts/v8.json"
        params = {
            'api_key': self.api_key,
            'lat': lat,
            'lon': lon,
            'system_capacity': 4,  # 4kW system
            'azimuth': 180,        # South facing
            'tilt': 20,            # 20 degree tilt
            'array_type': 1,       # Fixed roof mount
            'module_type': 0,      # Standard
            'losses': 14,          # 14% losses
            'timeframe': 'hourly'  # Get hourly data
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                
                if 'outputs' in data:
                    outputs = data['outputs']
                    
                    # Get just first 48 hours as sample
                    ac = outputs.get('ac', [])[:48]
                    dc = outputs.get('dc', [])[:48]
                    poa = outputs.get('poa', [])[:48]
                    tamb = outputs.get('tamb', [])[:48]
                    
                    records = []
                    base_time = pd.to_datetime('2024-01-01')
                    
                    for i in range(min(48, len(ac))):
                        record = {
                            'site_id': 'PVWATTS_SIM',
                            'timestamp': base_time + pd.Timedelta(hours=i),
                            'ac_power': ac[i] if i < len(ac) else 0,
                            'dc_power': dc[i] if i < len(dc) else 0,
                            'poa_irradiance': poa[i] if i < len(poa) else 0,
                            'ambient_temp': tamb[i] if i < len(tamb) else None,
                            'raw_json': json.dumps({'hour': i})
                        }
                        records.append(record)
                    
                    if records:
                        df = pd.DataFrame(records)
                        df.to_sql('nrel_pvdaq', self.engine, schema='api_ingest', 
                                 if_exists='append', index=False)
                        print(f"✅ Loaded {len(records)} hourly records")
                        
                        # Show sample
                        print("\nSample hourly data:")
                        for r in records[10:13]:  # Midday hours
                            print(f"  {r['timestamp'].strftime('%H:%M')}: AC={r['ac_power']:.0f}W, POA={r['poa_irradiance']:.0f}W/m²")
                        
                        return len(records)
                else:
                    print("❌ No outputs in response")
                    return 0
            else:
                print(f"❌ API error: {resp.status_code}")
                print(f"Response: {resp.text[:500]}")
                return 0
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0

if __name__ == "__main__":
    loader = NRELLoaderV2()
    
    # Test API first
    if loader.test_api():
        # Load monthly data
        loader.load_solar_resource_monthly()
        
        # Load hourly simulation
        loader.load_pvwatts_hourly()
