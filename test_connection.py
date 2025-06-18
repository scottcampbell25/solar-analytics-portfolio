#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

print("Testing PostgreSQL connection...")
print(f"Host: {os.getenv('DB_HOST', 'localhost')}")
print(f"User: {os.getenv('DB_USER', 'postgres')}")
print(f"Database: solar_analytics")

try:
    conn = psycopg2.connect(
        database='postgres',
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD')
    )
    print("✅ Connected to PostgreSQL!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
