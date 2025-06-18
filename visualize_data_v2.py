#!/usr/bin/env python3
"""Enhanced visualizations with feedback incorporated"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()

# Database connection
db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/solar_analytics"
engine = create_engine(db_url)

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("📊 Creating Enhanced Solar Analytics Visualizations...")

# 1. Enhanced Pipeline Summary (Stacked Bar)
try:
    # Get record counts with timing info
    weather_count = pd.read_sql("SELECT COUNT(*) as n FROM api_ingest.weather_test", engine)['n'][0]
    nrel_count = pd.read_sql("SELECT COUNT(*) as n FROM api_ingest.nrel_pvdaq", engine)['n'][0]
    forecast_count = pd.read_sql("SELECT COUNT(*) as n FROM api_ingest.tomorrow_weather", engine)['n'][0]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create stacked bar
    categories = ['Total Pipeline']
    weather_bar = [weather_count]
    nrel_bar = [nrel_count]
    forecast_bar = [forecast_count]
    
    # Create the bars
    p1 = ax.bar(categories, weather_bar, label=f'Weather (Real-time)', color='#FF6B6B')
    p2 = ax.bar(categories, nrel_bar, bottom=weather_bar, label=f'Solar Data (Hourly)', color='#4ECDC4')
    p3 = ax.bar(categories, forecast_bar, bottom=[weather_bar[0] + nrel_bar[0]], 
                label=f'Forecasts (10-min)', color='#45B7D1')
    
    # Add value labels
    ax.text(0, weather_count/2, f'{weather_count}', ha='center', va='center', fontsize=16, fontweight='bold')
    ax.text(0, weather_count + nrel_count/2, f'{nrel_count}', ha='center', va='center', fontsize=16, fontweight='bold')
    ax.text(0, weather_count + nrel_count + forecast_count/2, f'{forecast_count}', 
            ha='center', va='center', fontsize=16, fontweight='bold')
    
    # Total at top
    total = weather_count + nrel_count + forecast_count
    ax.text(0, total + 5, f'Total: {total}', ha='center', va='bottom', fontsize=18, fontweight='bold')
    
    ax.set_ylabel('Number of Records', fontsize=14)
    ax.set_title('Solar Analytics Data Pipeline Summary\n24-hour Ingestion Window', 
                 fontsize=16, fontweight='bold')
    ax.legend(loc='upper right')
    ax.set_ylim(0, total * 1.15)
    
    # Add update frequency annotations
    ax.text(1.02, 0.2, 'Update Frequency:', transform=ax.transAxes, fontsize=10, fontweight='bold')
    ax.text(1.02, 0.15, '• Weather: 15 min', transform=ax.transAxes, fontsize=9)
    ax.text(1.02, 0.10, '• Solar: 60 min', transform=ax.transAxes, fontsize=9)
    ax.text(1.02, 0.05, '• Forecast: 10 min', transform=ax.transAxes, fontsize=9)
    
    plt.tight_layout()
    plt.savefig('data_pipeline_summary_v2.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: data_pipeline_summary_v2.png")
    plt.close()
    
except Exception as e:
    print(f"❌ Pipeline summary error: {e}")

# 2. Enhanced Weather Forecast (with annotations)
try:
    tomorrow_df = pd.read_sql("""
        SELECT valid_time, temperature, cloud_cover, humidity
        FROM api_ingest.tomorrow_weather
        ORDER BY valid_time
        LIMIT 48
    """, engine)
    
    if len(tomorrow_df) > 0:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Temperature plot with high/low annotations
        ax1.plot(tomorrow_df['valid_time'], tomorrow_df['temperature'], 'r-', linewidth=2)
        ax1.fill_between(tomorrow_df['valid_time'], tomorrow_df['temperature'], alpha=0.3, color='red')
        
        # Find daily high/low
        tomorrow_df['date'] = pd.to_datetime(tomorrow_df['valid_time']).dt.date
        daily_stats = tomorrow_df.groupby('date')['temperature'].agg(['min', 'max'])
        
        # Annotate highs and lows
        for date, stats in daily_stats.iterrows():
            day_data = tomorrow_df[tomorrow_df['date'] == date]
            
            # High point
            high_idx = day_data['temperature'].idxmax()
            high_time = day_data.loc[high_idx, 'valid_time']
            high_temp = stats['max']
            ax1.annotate(f'{high_temp:.0f}°C', 
                        xy=(high_time, high_temp),
                        xytext=(0, 10), textcoords='offset points',
                        ha='center', fontweight='bold', color='darkred')
            
            # Low point
            low_idx = day_data['temperature'].idxmin()
            low_time = day_data.loc[low_idx, 'valid_time']
            low_temp = stats['min']
            ax1.annotate(f'{low_temp:.0f}°C',
                        xy=(low_time, low_temp),
                        xytext=(0, -15), textcoords='offset points',
                        ha='center', fontweight='bold', color='darkblue')
        
        ax1.set_ylabel('Temperature (°C)', fontsize=12)
        ax1.set_title('48-Hour Weather Forecast - Phoenix, AZ\nDiurnal High/Low Annotated', 
                     fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Cloud cover plot (with data or loading message)
        if tomorrow_df['cloud_cover'].notna().any():
            ax2.fill_between(tomorrow_df['valid_time'], tomorrow_df['cloud_cover'], 
                           alpha=0.5, color='gray')
            ax2.set_ylabel('Cloud Cover (%)', fontsize=12)
        else:
            ax2.text(0.5, 0.5, 'Cloud Cover Data Loading...', 
                    transform=ax2.transAxes, ha='center', va='center',
                    fontsize=16, color='gray', style='italic')
            ax2.set_ylabel('Cloud Cover (%)', fontsize=12, color='gray')
        
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('weather_forecast_v2.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: weather_forecast_v2.png")
        plt.close()
        
except Exception as e:
    print(f"❌ Weather forecast error: {e}")

# 3. Enhanced PV Output (with more data points and clipping zone)
try:
    # Get more data for better statistics
    pv_df = pd.read_sql("""
        SELECT timestamp, ac_power, dc_power, poa_irradiance
        FROM api_ingest.nrel_pvdaq
        WHERE site_id = 'PVWATTS_SIM' 
        AND timestamp IS NOT NULL
        AND poa_irradiance > 0
        ORDER BY timestamp
    """, engine)
    
    if len(pv_df) > 0:
        pv_df['hour'] = pd.to_datetime(pv_df['timestamp']).dt.hour
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Daily power curve with clipping zone
        hourly_avg = pv_df.groupby('hour')['ac_power'].mean()
        ax1.plot(hourly_avg.index, hourly_avg.values, 'b-', linewidth=3, label='Average Output')
        ax1.fill_between(hourly_avg.index, hourly_avg.values, alpha=0.3)
        
        # Add clipping zone (assuming 2600W inverter limit)
        inverter_limit = 2600
        ax1.axhspan(inverter_limit, 4000, alpha=0.2, color='red', label='Inverter Clipping Zone')
        ax1.axhline(y=inverter_limit, color='red', linestyle='--', alpha=0.5)
        ax1.text(12, inverter_limit + 50, 'Inverter Limit: 2,600W', 
                ha='center', fontsize=10, color='red')
        
        ax1.set_xlabel('Hour of Day', fontsize=12)
        ax1.set_ylabel('AC Power Output (W)', fontsize=12)
        ax1.set_title('4kW PV System - Daily Output Profile', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 23)
        ax1.legend()
        
        # Enhanced scatter plot with more points
        # Bin the data for cleaner visualization
        pv_df['irrad_bin'] = pd.cut(pv_df['poa_irradiance'], bins=20)
        binned = pv_df.groupby('irrad_bin').agg({
            'poa_irradiance': 'mean',
            'ac_power': ['mean', 'std', 'count']
        }).reset_index()
        
        # Filter bins with enough samples
        binned = binned[binned[('ac_power', 'count')] >= 2]
        
        if len(binned) > 5:
            x = binned[('poa_irradiance', 'mean')]
            y = binned[('ac_power', 'mean')]
            yerr = binned[('ac_power', 'std')]
            
            # Plot with error bars
            ax2.errorbar(x, y, yerr=yerr, fmt='o', alpha=0.6, capsize=5)
            
            # Fit regression with confidence interval
            from sklearn.linear_model import LinearRegression
            from scipy import stats
            
            X = x.values.reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            x_line = np.linspace(0, 1000, 100)
            y_pred = reg.predict(x_line.reshape(-1, 1))
            
            # Calculate confidence interval
            predict_mean_se = np.sqrt(np.sum((y - reg.predict(X))**2) / (len(y) - 2)) * \
                             np.sqrt(1/len(y) + (x_line - np.mean(x))**2 / np.sum((x - np.mean(x))**2))
            margin = 1.96 * predict_mean_se
            
            ax2.plot(x_line, y_pred, 'r-', label=f'Efficiency: {reg.coef_[0]:.2f} W/(W/m²)')
            ax2.fill_between(x_line, y_pred - margin, y_pred + margin, alpha=0.2, color='red')
            
            ax2.set_xlabel('Plane of Array Irradiance (W/m²)', fontsize=12)
            ax2.set_ylabel('AC Power Output (W)', fontsize=12)
            ax2.set_title(f'Power vs Irradiance ({len(pv_df)} data points)', 
                         fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # Add R-squared
            r2 = reg.score(X, y)
            ax2.text(0.05, 0.95, f'R² = {r2:.3f}', transform=ax2.transAxes, 
                    fontsize=10, verticalalignment='top')
        
        plt.tight_layout()
        plt.savefig('pv_system_output_v2.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: pv_system_output_v2.png")
        plt.close()
        
except Exception as e:
    print(f"❌ PV system plot error: {e}")

# 4. Enhanced Monthly Solar Resource (with nameplate reference)
try:
    monthly_df = pd.read_sql("""
        SELECT timestamp, ghi, dni
        FROM api_ingest.nrel_pvdaq
        WHERE site_id = 'NREL_MONTHLY'
        ORDER BY timestamp
    """, engine)
    
    if len(monthly_df) > 0:
        monthly_df['month'] = pd.to_datetime(monthly_df['timestamp']).dt.strftime('%b')
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        x = np.arange(len(monthly_df))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, monthly_df['ghi'], width, label='GHI', color='orange')
        bars2 = ax.bar(x + width/2, monthly_df['dni'], width, label='DNI', color='red')
        
        # Add nameplate reference line (typical requirement: 5 kWh/m²/day)
        nameplate_req = 5.0
        ax.axhline(y=nameplate_req, color='green', linestyle='--', linewidth=2, 
                  label=f'Nameplate Requirement ({nameplate_req} kWh/m²/day)')
        
        # Highlight surplus months
        for i, (ghi, dni) in enumerate(zip(monthly_df['ghi'], monthly_df['dni'])):
            if ghi >= nameplate_req:
                ax.add_patch(plt.Rectangle((i-width, 0), width*2, 10, 
                                         alpha=0.1, color='green'))
        
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Solar Irradiance (kWh/m²/day)', fontsize=12)
        ax.set_title('Monthly Solar Resource - Phoenix, AZ\nGreen shading indicates months exceeding nameplate requirement', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(monthly_df['month'], rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, max(monthly_df[['ghi', 'dni']].max()) * 1.2)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=9)
        
        plt.tight_layout()
        plt.savefig('solar_resource_monthly_v2.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: solar_resource_monthly_v2.png")
        plt.close()
        
except Exception as e:
    print(f"❌ Monthly solar plot error: {e}")

print("\n✨ Enhanced visualizations complete!")
print("\nImprovements made:")
print("- Stacked bar chart with update frequencies")
print("- Weather forecast with diurnal high/low annotations")
print("- PV output with inverter clipping zone and confidence intervals")
print("- Monthly solar with nameplate reference line")
