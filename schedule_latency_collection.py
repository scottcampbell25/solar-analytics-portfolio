#!/usr/bin/env python3
"""Schedule latency collection every 5 minutes"""

import schedule
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.etl.latency_collector import LatencyCollector
from build_api_health_panel import build_api_health_panel

def collect_and_build():
    """Collect latency and rebuild dashboard"""
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running latency collection...")
    
    try:
        # Collect latencies
        collector = LatencyCollector()
        results = collector.collect_all_latencies()
        
        # Clean old records weekly
        if time.strftime('%H:%M') == '00:00':
            collector.clean_old_records(days_to_keep=7)
        
        # Rebuild dashboard
        build_api_health_panel()
        
        print(f"✅ Collection complete: {len(results)} APIs monitored")
        
    except Exception as e:
        print(f"❌ Error in collection: {e}")

def run_scheduler():
    """Run the scheduler"""
    # Run immediately
    collect_and_build()
    
    # Schedule every 5 minutes
    schedule.every(5).minutes.do(collect_and_build)
    
    print("🕐 Latency collector started. Running every 5 minutes...")
    print("   Press Ctrl+C to stop")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler()
