#!/usr/bin/env python3
"""Debug Tomorrow.io API issues"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_tomorrow_api():
    """Test different Tomorrow.io endpoints"""
    api_key = os.getenv('TOMORROW_API_KEY')
    lat, lon = 33.4484, -112.0740
    
    print("Testing Tomorrow.io API...")
    print(f"API Key: {api_key[:10]}...")
    
    # Test 1: Current weather (realtime)
    print("\n1. Testing realtime endpoint...")
    url = "https://api.tomorrow.io/v4/weather/realtime"
    params = {
        'location': f'{lat},{lon}',
        'apikey': api_key,
        'units': 'metric'
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("   ✅ Realtime endpoint working")
            values = data.get('data', {}).get('values', {})
            print(f"   Current temp: {values.get('temperature', 'N/A')}°C")
        else:
            print(f"   ❌ Error: {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Forecast with different parameters
    print("\n2. Testing forecast endpoint (simplified)...")
    url = "https://api.tomorrow.io/v4/weather/forecast"
    params = {
        'location': f'{lat},{lon}',
        'apikey': api_key
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("   ✅ Forecast endpoint working")
            # Print structure
            print(f"   Response keys: {list(data.keys())}")
            if 'data' in data:
                print(f"   Data keys: {list(data['data'].keys())}")
                if 'timelines' in data['data']:
                    print(f"   Number of timelines: {len(data['data']['timelines'])}")
                    if data['data']['timelines']:
                        timeline = data['data']['timelines'][0]
                        print(f"   Timeline keys: {list(timeline.keys())}")
                        print(f"   Timestep: {timeline.get('timestep', 'N/A')}")
                        print(f"   Intervals: {len(timeline.get('intervals', []))}")
        else:
            print(f"   ❌ Error: {resp.text[:500]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Try with explicit fields
    print("\n3. Testing with explicit fields...")
    url = "https://api.tomorrow.io/v4/weather/forecast"
    params = {
        'location': f'{lat},{lon}',
        'apikey': api_key,
        'units': 'metric',
        'timesteps': ['1h'],
        'fields': ['temperature', 'cloudCover']
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("   ✅ Working with explicit fields")
            
            # Save response for inspection
            with open('tomorrow_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("   💾 Saved full response to tomorrow_response.json")
            
            # Try to extract some data
            if 'data' in data and 'timelines' in data['data']:
                timelines = data['data']['timelines']
                if timelines and 'intervals' in timelines[0]:
                    intervals = timelines[0]['intervals']
                    print(f"   Found {len(intervals)} forecast intervals")
                    if intervals:
                        first = intervals[0]
                        print(f"   First interval: {first.get('startTime', 'N/A')}")
                        values = first.get('values', {})
                        print(f"   Temperature: {values.get('temperature', 'N/A')}°C")
                        print(f"   Cloud cover: {values.get('cloudCover', 'N/A')}%")
        else:
            print(f"   ❌ Error: {resp.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_tomorrow_api()
