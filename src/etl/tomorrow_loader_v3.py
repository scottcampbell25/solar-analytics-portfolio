#!/usr/bin/env python3
"""Tomorrow.io Weather Forecast Loader - Final fixed version"""

import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import requests
import json

load_dotenv()

class TomorrowLoaderV3:
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
            'fields': ['temperature', 'cloudCover', 'humidity', 'windSpeed', 'dewPoint', 'precipitationProbability']
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                
                records = []
                forecast_time = datetime.utcnow()
                
                # The structure has timelines as a dict with 'hourly' key
                timelines = data.get('timelines', {})
                hourly_data = timelines.get('hourly', [])
                
                if hourly_data:
                    # Process hourly intervals (limit to 48 hours)
                    for interval in hourly_data[:48]:
                        values = interval.get('values', {})
                        
                        record = {
                            'location_lat': lat,
                            'location_lon': lon,
                            'forecast_time': forecast_time,
                            'valid_time': pd.to_datetime(interval.get('time')),
                            'temperature': values.get('temperature'),
                            'solar_ghi': 0,  # Not available in this response
                            'solar_dni': 0,  # Not available in this response
                            'cloud_cover': values.get('cloudCover'),
                            'precipitation_intensity': values.get('precipitationProbability', 0),
                            'raw_json': json.dumps(interval)
                        }
                        
                        # Add extra fields we got
                        record['humidity'] = values.get('humidity')
                        record['wind_speed'] = values.get('windSpeed')
                        record['dew_point'] = values.get('dewPoint')
                        
                        records.append(record)
                
                if records:
                    df = pd.DataFrame(records)
                    
                    # Add the extra columns to our table if they don't exist
                    with self.engine.connect() as conn:
                        # Add columns if they don't exist
                        try:
                            conn.execute(text("""
                                ALTER TABLE api_ingest.tomorrow_weather 
                                ADD COLUMN IF NOT EXISTS humidity FLOAT,
                                ADD COLUMN IF NOT EXISTS wind_speed FLOAT,
                                ADD COLUMN IF NOT EXISTS dew_point FLOAT;
                            """))
                            conn.commit()
                        except:
                            pass  # Columns might already exist
                    
                    # Save to database
                    df.to_sql('tomorrow_weather', self.engine, schema='api_ingest',
                             if_exists='append', index=False)
                    print(f"✅ Loaded {len(records)} forecast records")
                    
                    # Show sample
                    print("\nSample forecast (next 6 hours):")
                    for r in records[:6]:
                        print(f"  {r['valid_time'].strftime('%m-%d %H:%M')}: "
                              f"{r['temperature']:.1f}°C, "
                              f"Cloud={r['cloud_cover']:.0f}%, "
                              f"Humidity={r['humidity']:.0f}%")
                    
                    # Show daily summary
                    df['date'] = pd.to_datetime(df['valid_time']).dt.date
                    df['hour'] = pd.to_datetime(df['valid_time']).dt.hour
                    
                    # Daily temperature summary
                    daily_summary = df.groupby('date').agg({
                        'temperature': ['min', 'max', 'mean'],
                        'cloud_cover': 'mean',
                        'humidity': 'mean'
                    }).round(1)
                    
                    print("\nDaily forecast summary:")
                    for date, row in daily_summary.iterrows():
                        print(f"  {date}: Temp {row[('temperature', 'min')]}°C to {row[('temperature', 'max')]}°C, "
                              f"Avg cloud {row[('cloud_cover', 'mean')]}%")
                    
                    # Check for clear sky hours (good for solar)
                    clear_hours = df[df['cloud_cover'] < 20]
                    if len(clear_hours) > 0:
                        print(f"\n☀️  Clear sky hours (cloud < 20%): {len(clear_hours)} out of {len(df)}")
                    
                    return len(records)
                else:
                    print("❌ No forecast data found")
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

if __name__ == "__main__":
    loader = TomorrowLoaderV3()
    loader.load_forecast()
