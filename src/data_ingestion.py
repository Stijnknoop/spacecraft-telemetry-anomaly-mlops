# Standard library imports
from datetime import datetime, timedelta
import os

# Third-party library imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ... [keep generate_satellite_telemetry and generate_space_weather_data exactly the same] ...

def main():
    print("🛰️ Starting Data Ingestion Pipeline for Project ASTRA...")
    start_date = datetime(2026, 7, 1, 0, 0, 0)
    periods = 1440  
    
    telemetry_data = generate_satellite_telemetry(start_date, periods)
    space_weather_data = generate_space_weather_data(start_date, periods)
    
    telemetry_data = telemetry_data.sort_values("timestamp")
    space_weather_data = space_weather_data.sort_values("env_timestamp")
    
    unified_dataset = pd.merge_asof(
        telemetry_data, 
        space_weather_data, 
        left_on="timestamp", 
        right_on="env_timestamp", 
        direction="backward"
    )
    unified_dataset = unified_dataset.drop(columns=["env_timestamp"]).ffill().bfill()
    
    # Updated to strict industry-standard paths
    os.makedirs("data/raw", exist_ok=True)
    
    csv_output_path = "data/raw/telemetry_space_weather.csv"
    unified_dataset.to_csv(csv_output_path, index=False)
    print(f"✅ Raw dataset saved to: {csv_output_path}")
    
    plot_output_path = "data/raw/telemetry_anomaly_plot.png"
    # (Assuming your save_telemetry_plots function is kept above)
    save_telemetry_plots(unified_dataset, plot_output_path)

if __name__ == "__main__":
    main()
