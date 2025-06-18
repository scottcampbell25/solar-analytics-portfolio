#!/usr/bin/env python3
"""Quick visualization of solar analytics data"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

# Database connection
db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
engine = create_engine(db_url)

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("📊 Creating Solar Analytics Visualizations...")

# 1. Temperature trends from Tomorrow.io
try:
    tomorrow_df = pd.read_sql("""
        SELECT valid_time, temperature, cloud_cover, humidity
        FROM api_ingest.tomorrow_weather
        ORDER BY valid_time
        LIMIT 48
    """, engine)
    
    if len(tomorrow_df) > 0:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Temperature plot
        ax1.plot(tomorrow_df['valid_time'], tomorrow_df['temperature'], 'r-', linewidth=2)
        ax1.fill_between(tomorrow_df['valid_time'], tomorrow_df['temperature'], alpha=0.3, color='red')
        ax1.set_ylabel('Temperature (°C)', fontsize=12)
        ax1.set_title('48-Hour Weather Forecast - Phoenix, AZ', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Cloud cover plot
        ax2.fill_between(tomorrow_df['valid_time'], tomorrow_df['cloud_cover'], alpha=0.5, color='gray')
        ax2.set_ylabel('Cloud Cover (%)', fontsize=12)
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('weather_forecast.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: weather_forecast.png")
        plt.close()
except Exception as e:
    print(f"❌ Could not create weather forecast plot: {e}")

# 2. Solar resource by month
try:
    monthly_df = pd.read_sql("""
        SELECT timestamp, ghi, dni
        FROM api_ingest.nrel_pvdaq
        WHERE site_id = 'NREL_MONTHLY'
        ORDER BY timestamp
    """, engine)
    
    if len(monthly_df) > 0:
        monthly_df['month'] = pd.to_datetime(monthly_df['timestamp']).dt.strftime('%B')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = range(len(monthly_df))
        width = 0.35
        
        bars1 = ax.bar([i - width/2 for i in x], monthly_df['ghi'], width, label='GHI', color='orange')
        bars2 = ax.bar([i + width/2 for i in x], monthly_df['dni'], width, label='DNI', color='red')
        
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Solar Irradiance (kWh/m²/day)', fontsize=12)
        ax.set_title('Monthly Solar Resource - Phoenix, AZ', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(monthly_df['month'], rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=8)
        
        plt.tight_layout()
        plt.savefig('solar_resource_monthly.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: solar_resource_monthly.png")
        plt.close()
except Exception as e:
    print(f"❌ Could not create monthly solar plot: {e}")

# 3. PV system simulation
try:
    pv_df = pd.read_sql("""
        SELECT timestamp, ac_power, poa_irradiance
        FROM api_ingest.nrel_pvdaq
        WHERE site_id = 'PVWATTS_SIM' AND timestamp IS NOT NULL
        ORDER BY timestamp
        LIMIT 48
    """, engine)
    
    if len(pv_df) > 0:
        pv_df['hour'] = pd.to_datetime(pv_df['timestamp']).dt.hour
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Daily power curve
        ax1.plot(pv_df['hour'], pv_df['ac_power'], 'b-', linewidth=3)
        ax1.fill_between(pv_df['hour'], pv_df['ac_power'], alpha=0.3)
        ax1.set_xlabel('Hour of Day', fontsize=12)
        ax1.set_ylabel('AC Power Output (W)', fontsize=12)
        ax1.set_title('4kW PV System - Daily Output Profile', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 23)
        
        # Scatter plot of irradiance vs power
        ax2.scatter(pv_df['poa_irradiance'], pv_df['ac_power'], alpha=0.6, s=50)
        ax2.set_xlabel('Plane of Array Irradiance (W/m²)', fontsize=12)
        ax2.set_ylabel('AC Power Output (W)', fontsize=12)
        ax2.set_title('Power vs Irradiance Relationship', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add efficiency line
        if len(pv_df[pv_df['poa_irradiance'] > 0]) > 0:
            from sklearn.linear_model import LinearRegression
            X = pv_df[pv_df['poa_irradiance'] > 0]['poa_irradiance'].values.reshape(-1, 1)
            y = pv_df[pv_df['poa_irradiance'] > 0]['ac_power'].values
            reg = LinearRegression().fit(X, y)
            x_line = [[0], [1000]]
            y_line = reg.predict(x_line)
            ax2.plot([0, 1000], y_line, 'r--', label=f'Efficiency: {reg.coef_[0]:.2f} W/(W/m²)')
            ax2.legend()
        
        plt.tight_layout()
        plt.savefig('pv_system_output.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: pv_system_output.png")
        plt.close()
except Exception as e:
    print(f"❌ Could not create PV system plot: {e}")

# 4. Data pipeline summary
try:
    # Get record counts
    counts = {}
    tables = [
        ('api_ingest.weather_test', 'Weather'),
        ('api_ingest.nrel_pvdaq', 'Solar Data'),
        ('api_ingest.tomorrow_weather', 'Forecasts')
    ]
    
    for table, name in tables:
        try:
            count = pd.read_sql(f"SELECT COUNT(*) as n FROM {table}", engine)['n'][0]
            counts[name] = count
        except:
            counts[name] = 0
    
    if sum(counts.values()) > 0:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        bars = ax.bar(counts.keys(), counts.values(), color=colors)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Number of Records', fontsize=12)
        ax.set_title('Solar Analytics Data Pipeline - Record Counts', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add total
        total = sum(counts.values())
        ax.text(0.5, 0.95, f'Total Records: {total:,}', 
               transform=ax.transAxes, ha='center', fontsize=14,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig('data_pipeline_summary.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: data_pipeline_summary.png")
        plt.close()
except Exception as e:
    print(f"❌ Could not create summary plot: {e}")

print("\n✨ Visualization complete! Check the PNG files in your directory.")
print("\nYou can include these in your portfolio:")
print("- weather_forecast.png - Shows temperature and cloud cover predictions")
print("- solar_resource_monthly.png - Shows seasonal solar patterns")
print("- pv_system_output.png - Shows PV system performance")
print("- data_pipeline_summary.png - Shows your data collection success")
