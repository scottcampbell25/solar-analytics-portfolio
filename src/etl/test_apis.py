#!/usr/bin/env python3
"""Test all API connections"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("Testing API connections...")

# Test NREL
print("\n1. Testing NREL API...")
try:
    url = f"https://developer.nrel.gov/api/alt-fuel-stations/v1.json?limit=1&api_key={os.getenv('NREL_API_KEY')}"
    resp = requests.get(url, timeout=10)
    print(f"   NREL: {resp.status_code} - {'✅ OK' if resp.status_code == 200 else '❌ Failed'}")
    if resp.status_code != 200:
        print(f"   Response: {resp.text[:200]}")
except Exception as e:
    print(f"   NREL: ❌ Error - {e}")

# Test Tomorrow.io
print("\n2. Testing Tomorrow.io API...")
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
print("\n3. Testing OpenWeather API...")
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
print("\n4. Testing NOAA API...")
try:
    url = "https://api.weather.gov/points/33.4484,-112.0740"
    headers = {'User-Agent': 'SolarAnalytics/1.0'}
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"   NOAA: {resp.status_code} - {'✅ OK' if resp.status_code == 200 else '❌ Failed'}")
except Exception as e:
    print(f"   NOAA: ❌ Error - {e}")

print("\n✅ API test complete!")
