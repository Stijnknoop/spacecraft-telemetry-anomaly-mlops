# Standard library imports
from datetime import datetime, timedelta
import os

# Third-party library imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def generate_satellite_telemetry(start_time: datetime, periods: int) -> pd.DataFrame:
    """
    Simulates high-frequency technical and operational satellite telemetry data.
    Introduces a specific anomaly (power drop and temperature spike) midway.
    """
    timestamps = [start_time + timedelta(minutes=5 * i) for i in range(periods)]
    
    # Base operational data (normal behavior)
    np.random.seed(42)
    solar_current = np.random.normal(loc=12.0, scale=0.5, size=periods) # Amps
    battery_temp = np.random.normal(loc=22.0, scale=1.0, size=periods)  # Celsius
    bus_voltage = np.random.normal(loc=28.0, scale=0.1, size=periods)   # Volts
    
    # Introduce a severe operational anomaly (Simulating Solar Flare Impact)
    # This occurs in the last 25% of the time-series
    anomaly_start = int(periods * 0.75)
    
    # Solar panels degrade, battery heats up, voltage drops slightly
    solar_current[anomaly_start:] -= np.random.uniform(4.0, 6.0, size=periods - anomaly_start)
    battery_temp[anomaly_start:] += np.random.uniform(15.0, 25.0, size=periods - anomaly_start)
    bus_voltage[anomaly_start:] -= np.random.uniform(1.5, 2.5, size=periods - anomaly_start)
    
    telemetry_df = pd.DataFrame({
        "timestamp": timestamps,
        "solar_panel_current_A": solar_current,
        "battery_temperature_C": battery_temp,
        "bus_voltage_V": bus_voltage
    })
    
    return telemetry_df

def generate_space_weather_data(start_time: datetime, periods: int) -> pd.DataFrame:
    """
    Simulates external environmental data (Space Weather / Solar Flare Index).
    Correlates a massive solar flare activity spikes with the telemetry anomaly.
    """
    # Environmental metrics are captured on a slightly different offset (e.g., every 15 minutes)
    # This demonstrates your ability to align heterogeneous datasets
    weather_periods = periods // 3
    timestamps = [start_time + timedelta(minutes=15 * i) for i in range(weather_periods)]
    
    # Base solar activity (Kp index usually ranges from 0-9)
    np.random.seed(24)
    kp_index = np.random.uniform(1.0, 3.0, size=weather_periods)
    solar_flux_index = np.random.normal(loc=70.0, scale=5.0, size=weather_periods)
    
    # Simulate a massive Solar Storm triggering the anomaly
    anomaly_start = int(weather_periods * 0.75)
    kp_index[anomaly_start:] = np.random.uniform(7.0, 9.0, size=weather_periods - anomaly_start)
    solar_flux_index[anomaly_start:] += np.random.uniform(150.0, 200.0, size=weather_periods - anomaly_start)
    
    weather_df = pd.DataFrame({
        "env_timestamp": timestamps,
        "kp_index": kp_index,
        "solar_flux_index_sfu": solar_flux_index
    })
    
    return weather_df

def save_telemetry_plots(df: pd.DataFrame, output_path: str):
    """
    Generates and saves exploratory data analysis plots showing the telemetry variables
    and the corresponding space weather anomaly window.
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # Plot 1: Solar Panel Current
    axes[0].plot(df["timestamp"], df["solar_panel_current_A"], color="tab:blue", label="Solar Panel Current (A)")
    axes[0].set_ylabel("Current (A)")
    axes[0].set_title("Satellite Telemetry & Space Weather Correlation (Project ASTRA)", fontsize=14, fontweight='bold')
    axes[0].grid(True, linestyle="--", alpha=0.5)
    axes[0].legend(loc="upper left")

    # Plot 2: Battery Temperature
    axes[1].plot(df["timestamp"], df["battery_temperature_C"], color="tab:red", label="Battery Temperature (°C)")
    axes[1].set_ylabel("Temperature (°C)")
    axes[1].grid(True, linestyle="--", alpha=0.5)
    axes[1].legend(loc="upper left")

    # Plot 3: Kp Index (Space Weather Indicator)
    axes[2].plot(df["timestamp"], df["kp_index"], color="tab:orange", label="Space Weather Kp Index (0-9)")
    axes[2].set_ylabel("Kp Index")
    axes[2].set_xlabel("Timestamp")
    axes[2].grid(True, linestyle="--", alpha=0.5)
    axes[2].legend(loc="upper left")

    # Draw a vertical dashed line to mark the exact moment the Solar Storm hits the timeline
    anomaly_start_idx = int(len(df) * 0.75)
    anomaly_time = df["timestamp"].iloc[anomaly_start_idx]
    
    for ax in axes:
        ax.axvline(x=anomaly_time, color="darkred", linestyle=":", linewidth=2.5)
        if ax == axes[0]:
            ax.text(anomaly_time, ax.get_ylim()[1] * 0.85, '  Solar Storm Impact Event', color='darkred', fontweight='bold', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"📊 Visualization plots successfully saved to: {output_path}")

def main():
    print("🛰️ Starting Data Ingestion Pipeline for Project ASTRA...")
    
    # Define timeframe (5 days of data generation)
    start_date = datetime(2026, 7, 1, 0, 0, 0)
    periods = 1440  # 5 days in 5-minute intervals
    
    # 1. Fetch/Generate the distinct data domains
    print("📊 Generating domain 1: Technical & Operational Telemetry...")
    telemetry_data = generate_satellite_telemetry(start_date, periods)
    
    print("☀️ Generating domain 2: External Environmental Space Weather...")
    space_weather_data = generate_space_weather_data(start_date, periods)
    
    # 2. Make data interoperable (Merge heterogeneous datasets based on time alignment)
    print("🔄 Aligning heterogeneous datasets into a unified AI-ready structure...")
    
    telemetry_data = telemetry_data.sort_values("timestamp")
    space_weather_data = space_weather_data.sort_values("env_timestamp")
    
    # Merge the nearest environmental weather data to each telemetry log
    unified_dataset = pd.merge_asof(
        telemetry_data, 
        space_weather_data, 
        left_on="timestamp", 
        right_on="env_timestamp", 
        direction="backward"
    )
    
    # Drop the duplicate timestamp column used for alignment
    unified_dataset = unified_dataset.drop(columns=["env_timestamp"])
    
    # 3. Clean and Validate
    unified_dataset = unified_dataset.ffill().bfill()
    
    # 4. Save CSV and Plot Artifacts
    os.makedirs("data", exist_ok=True)
    
    # Save Dataset
    csv_output_path = "data/telemetry_space_weather.csv"
    unified_dataset.to_csv(csv_output_path, index=False)
    print(f"✅ AI-ready dataset saved to: {csv_output_path}")
    
    # Save Plot
    plot_output_path = "data/telemetry_anomaly_plot.png"
    save_telemetry_plots(unified_dataset, plot_output_path)
    
    print(f"📊 Total Records Processed: {len(unified_dataset)}")

if __name__ == "__main__":
    main()
  
