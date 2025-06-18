#!/usr/bin/env python3
"""Collect API latency metrics for monitoring"""

import os
import time
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LatencyCollector:
    """Collect and store API latency metrics"""
    
    def __init__(self):
        self.engine = self._get_db_engine()
        self.apis = {
            'NREL': {
                'url': 'https://developer.nrel.gov/api/alt-fuel-stations/v1.json',
                'params': {'limit': 1, 'api_key': os.getenv('NREL_API_KEY')},
                'timeout': 5
            },
            'OpenWeather': {
                'url': 'https://api.openweathermap.org/data/2.5/weather',
                'params': {'lat': 33.4484, 'lon': -112.0740, 'appid': os.getenv('OPENWEATHER_API_KEY')},
                'timeout': 5
            },
            'Tomorrow.io': {
                'url': 'https://api.tomorrow.io/v4/weather/realtime',
                'params': {'location': '33.4484,-112.0740', 'apikey': os.getenv('TOMORROW_API_KEY')},
                'timeout': 5
            }
        }
    
    def _get_db_engine(self):
        """Create database connection"""
        db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
        return create_engine(db_url)
    
    def ping_api(self, api_name, config):
        """Ping an API and measure latency"""
        try:
            # Use HEAD request if possible, otherwise lightweight GET
            start = time.perf_counter()
            
            if api_name == 'NREL':
                # NREL doesn't support HEAD, use minimal GET
                response = requests.get(config['url'], params=config['params'], timeout=config['timeout'])
            else:
                # Try HEAD first
                try:
                    response = requests.head(config['url'], params=config['params'], timeout=config['timeout'])
                except:
                    # Fall back to GET
                    response = requests.get(config['url'], params=config['params'], timeout=config['timeout'])
            
            latency_ms = (time.perf_counter() - start) * 1000
            
            return {
                'api_name': api_name,
                'latency_ms': round(latency_ms, 2),
                'status_code': response.status_code,
                'success': response.status_code < 400,
                'timestamp': datetime.utcnow()
            }
            
        except requests.exceptions.Timeout:
            return {
                'api_name': api_name,
                'latency_ms': config['timeout'] * 1000,
                'status_code': 0,
                'success': False,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Error pinging {api_name}: {e}")
            return {
                'api_name': api_name,
                'latency_ms': 9999,
                'status_code': 0,
                'success': False,
                'timestamp': datetime.utcnow()
            }
    
    def collect_all_latencies(self):
        """Collect latency for all APIs"""
        results = []
        
        for api_name, config in self.apis.items():
            result = self.ping_api(api_name, config)
            results.append(result)
            logger.info(f"{api_name}: {result['latency_ms']}ms (status: {result['status_code']})")
        
        # Store in database
        if results:
            with self.engine.connect() as conn:
                for result in results:
                    conn.execute(text("""
                        INSERT INTO api_ingest.latency_history 
                        (timestamp, api_name, latency_ms, status_code, success)
                        VALUES (:timestamp, :api_name, :latency_ms, :status_code, :success)
                    """), result)
                conn.commit()
        
        return results
    
    def get_sparkline_data(self):
        """Get sparkline data for all APIs"""
        query = """
            SELECT 
                api_name,
                ARRAY_AGG(latency_ms ORDER BY timestamp) AS series,
                AVG(latency_ms) AS avg_latency,
                MIN(latency_ms) AS min_latency,
                MAX(latency_ms) AS max_latency,
                COUNT(*) FILTER (WHERE success = TRUE) AS success_count,
                COUNT(*) AS total_count
            FROM (
                SELECT * FROM api_ingest.latency_history
                WHERE timestamp > NOW() - INTERVAL '4 hours'
                ORDER BY timestamp DESC
                LIMIT 300
            ) t
            GROUP BY api_name
            ORDER BY api_name;
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchall()
    
    def clean_old_records(self, days_to_keep=7):
        """Clean records older than specified days"""
        with self.engine.connect() as conn:
            conn.execute(text(f"""
                DELETE FROM api_ingest.latency_history
                WHERE timestamp < NOW() - INTERVAL '{days_to_keep} days'
            """))
            conn.commit()
            logger.info(f"Cleaned records older than {days_to_keep} days")

if __name__ == "__main__":
    collector = LatencyCollector()
    
    # Collect current latencies
    print("Collecting API latencies...")
    results = collector.collect_all_latencies()
    
    # Get sparkline data
    print("\nSparkline data:")
    sparkline_data = collector.get_sparkline_data()
    for row in sparkline_data:
        print(f"{row.api_name}: {len(row.series) if row.series else 0} points, "
              f"avg={row.avg_latency:.1f}ms, "
              f"uptime={row.success_count/row.total_count*100:.1f}%")
