#!/usr/bin/env python3
import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

# Connect to PostgreSQL
try:
    # First create the database
    conn = psycopg2.connect(
        database='postgres',
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD')
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Create database if not exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'solar_analytics'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE solar_analytics")
        print("✅ Created database: solar_analytics")
    else:
        print("✅ Database already exists")
    
    cur.close()
    conn.close()
    
    # Now connect to the new database and create schemas
    conn = psycopg2.connect(
        database='solar_analytics',
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    
    # Create schemas
    cur.execute("CREATE SCHEMA IF NOT EXISTS api_ingest;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS mart;")
    print("✅ Created schemas")
    
    # Create simple table for testing
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_ingest.test_table (
            id SERIAL PRIMARY KEY,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Created test table")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("✅ Database setup complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
