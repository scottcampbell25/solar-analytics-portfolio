#!/usr/bin/env python3
"""Create latency tracking table and functions"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def setup_latency_tracking():
    """Create latency history table for API monitoring"""
    
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Create latency history table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_ingest.latency_history (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                api_name VARCHAR(50) NOT NULL,
                latency_ms FLOAT NOT NULL CHECK (latency_ms >= 0 AND latency_ms < 10000),
                status_code INTEGER,
                success BOOLEAN DEFAULT TRUE
            );
        """))
        
        # Create index for efficient queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_latency_timestamp 
            ON api_ingest.latency_history(timestamp DESC);
        """))
        
        # Create index for API name queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_latency_api_name 
            ON api_ingest.latency_history(api_name, timestamp DESC);
        """))
        
        # Create a view for last 24 hours
        conn.execute(text("""
            CREATE OR REPLACE VIEW api_ingest.latency_24h AS
            SELECT 
                api_name,
                timestamp,
                latency_ms,
                status_code,
                success
            FROM api_ingest.latency_history
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            ORDER BY api_name, timestamp DESC;
        """))
        
        # Create aggregated view for sparklines
        conn.execute(text("""
            CREATE OR REPLACE VIEW api_ingest.latency_sparkline AS
            SELECT 
                api_name,
                ARRAY_AGG(latency_ms ORDER BY timestamp DESC) 
                    FILTER (WHERE timestamp > NOW() - INTERVAL '4 hours') AS sparkline_4h,
                AVG(latency_ms) 
                    FILTER (WHERE timestamp > NOW() - INTERVAL '4 hours') AS avg_4h,
                MAX(latency_ms) 
                    FILTER (WHERE timestamp > NOW() - INTERVAL '4 hours') AS max_4h,
                MIN(latency_ms) 
                    FILTER (WHERE timestamp > NOW() - INTERVAL '4 hours') AS min_4h,
                COUNT(*) 
                    FILTER (WHERE timestamp > NOW() - INTERVAL '4 hours' AND success = TRUE) AS success_count_4h,
                COUNT(*) 
                    FILTER (WHERE timestamp > NOW() - INTERVAL '4 hours') AS total_count_4h
            FROM api_ingest.latency_history
            WHERE timestamp > NOW() - INTERVAL '4 hours'
            GROUP BY api_name;
        """))
        
        conn.commit()
        
    print("✅ Created latency tracking schema:")
    print("   - api_ingest.latency_history table")
    print("   - Indexes for efficient queries")
    print("   - latency_24h view")
    print("   - latency_sparkline view")

if __name__ == "__main__":
    setup_latency_tracking()
