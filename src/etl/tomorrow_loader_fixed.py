#!/usr/bin/env python3
"""Tomorrow.io Weather Forecast Loader - Fixed version"""

import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import requests
import json

load_dotenv()

class TomorrowLoader:
    def __init__(self):
        self.api_key = os.getenv('TOMORROW_API_KEY')
        self.engine = self._get_db_engine()
    
    def _get_db_engine(self):
        db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
        return create_engine(db_url)
    
    def load_forecast(self, lat=33.4484, lon=-112.0740):
        """Load weather forecast from Tomorrow.io"""
        print(f"Loading Tomorrow.io forecast for {lat}, {lon}...")
        
        url = "https://api.tomorrow.io/v4/weather/forecast"
        
        params = {
            'location': f'{lat},{lon}',
            'apikey': self.api_key,
            'units': 'metric',
            'timesteps': ['1h'],
            'fields': ['temperature', 'cloudCover', 'solarGHI', 'solarDNI', 'precipitationIntensity', 'humidity', 'windSpeed']
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                
                records = []
                forecast_time = datetime.utcnow()
                
                # The structure is different - timelines is at the top level
                timelines = data.get('timelines', [])
                
                if timelines:
                    # Get the hourly timeline
                    hourly_timeline = None
                    for timeline in timelines:
                        if timeline.get('timestep') == '1h':
                            hourly_timeline = timeline
                            break
                    
                    if hourly_timeline and 'intervals' in hourly_timeline:
                        intervals = hourly_timeline['intervals'][:48]  # Next 48 hours
                        
                        for interval in intervals:
                            values = interval.get('values', {})
                            
                            record = {
                                'location_lat': lat,
                                'location_lon': lon,
                                'forecast_time': forecast_time,
                                'valid_time': pd.to_datetime(interval['startTime']),
                                'temperature': values.get('temperature'),
                                'solar_ghi': values.get('solarGHI', 0),
                                'solar_dni': values.get('solarDNI', 0),
                                'cloud_cover': values.get('cloudCover'),
                                'precipitation_intensity': values.get('precipitationIntensity', 0),
                                'raw_json': json.dumps(interval)
                            }
                            records.append(record)
                
                if records:
                    df = pd.DataFrame(records)
                    df.to_sql('tomorrow_weather', self.engine, schema='api_ingest',
                             if_exists='append', index=False)
                    print(f"✅ Loaded {len(records)} forecast records")
                    
                    # Show sample
                    print("\nSample forecast (next 6 hours):")
                    for r in records[:6]:
                        print(f"  {r['valid_time'].strftime('%m-%d %H:%M')}: {r['temperature']:.1f}°C, GHI={r['solar_ghi']:.0f}W/m², Cloud={r['cloud_cover']:.0f}%")
                    
                    # Show daily summary
                    df['date'] = pd.to_datetime(df['valid_time']).dt.date
                    daily_summary = df.groupby('date').agg({
                        'temperature': ['min', 'max', 'mean'],
                        'solar_ghi': ['max', 'mean'],
                        'cloud_cover': 'mean'
                    }).round(1)
                    
                    print("\nDaily forecast summary:")
                    print(daily_summary)
                    
                    return len(records)
                else:
                    print("❌ No forecast data found")
                    print(f"Response structure: {json.dumps(data, indent=2)[:500]}")
                    return 0
            else:
                print(f"❌ API error: {resp.status_code}")
                print(f"Response: {resp.text[:500]}")
                return 0
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def load_realtime(self, lat=33.4484, lon=-112.0740):
        """Load current conditions from Tomorrow.io"""
        print(f"\nLoading Tomorrow.io realtime data...")
        
        url = "https://api.tomorrow.io/v4/weather/realtime"
        
        params = {
            'location': f'{lat},{lon}',
            'apikey': self.api_key,
            'units': 'metric',
            'fields': ['temperature', 'cloudCover', 'solarGHI', 'humidity', 'windSpeed']
        }
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                values = data.get('data', {}).get('values', {})
                
                print(f"✅ Current conditions:")
                print(f"   Temperature: {values.get('temperature', 'N/A')}°C")
                print(f"   Cloud cover: {values.get('cloudCover', 'N/A')}%")
                print(f"   Solar GHI: {values.get('solarGHI', 'N/A')}W/m²")
                print(f"   Humidity: {values.get('humidity', 'N/A')}%")
                
                return values
            else:
                print(f"❌ API error: {resp.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

if __name__ == "__main__":
    loader = TomorrowLoader()
    
    # Load current conditions
    loader.load_realtime()
    
    # Load forecast
    loader.load_forecast()
