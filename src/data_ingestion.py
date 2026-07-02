# Standard library imports
from datetime import datetime, timedelta
import os

# Third-party library imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_full_space_weather_data(start_time: datetime, periods: int) -> pd.DataFrame:
    """
    Simulates continuous external environmental data (Space Weather / Solar Flare Index)
    over a full 1440-period time series, with a smooth, continuous peak for a solar flare event.
    """
    np.random.seed(24)
    timestamps = [start_time + timedelta(minutes=5 * i) for i in range(periods)]
    
    # 1. Base solar activity: smooth continuous fluctuations (Kp 1-3) using a smoothed random walk
    kp_base = np.random.uniform(1.0, 3.0, size=periods)
    # Smooth it (using a rolling moving average for continuous look, window = 1 hour)
    window = 12 
    kp_base_smooth = pd.Series(kp_base).rolling(window=window, min_periods=1).mean().values
    
    solar_flux_base = np.random.normal(loc=70.0, scale=5.0, size=periods)
    solar_flux_base_smooth = pd.Series(solar_flux_base).rolling(window=window, min_periods=1).mean().values
    
    # 2. Injected Solar Flare Event during the last 25% of the full periods (points 1080-1440)
    anomaly_start_idx = int(periods * 0.75)
    pulse_length = periods - anomaly_start_idx # 360 points (1.25 days)
    
    # Define a smooth, slightly asymmetric Gaussian pulse for the Kp peak
    t_pulse = np.linspace(0, 1, pulse_length)
    t_peak_relative = 0.3 # peak is earlier than end (30% in)
    sigma_kp = 0.1 # pulse width
    # Scale peak amplitude addition (peak around Kp 7-9 total)
    A_kp = np.random.uniform(5.0, 7.0) 
    
    kp_flare_pulse = A_kp * np.exp(-(t_pulse - t_peak_relative)**2 / (2 * sigma_kp**2))
    
    # Correlated but slightly delayed and wider Solar Flux pulse
    A_flux = A_kp * np.random.uniform(25.0, 35.0)
    solar_flux_flare_pulse = A_flux * np.exp(-(t_pulse - (t_peak_relative + 0.05))**2 / (2 * (sigma_kp*1.2)**2))
    
    # 3. Combine base and injected pulse for full time series
    kp_index = kp_base_smooth.copy()
    solar_flux_index = solar_flux_base_smooth.copy()
    
    kp_index[anomaly_start_idx:] += kp_flare_pulse
    solar_flux_index[anomaly_start_idx:] += solar_flux_flare_pulse
    
    # Final data frame (full time series)
    full_weather_df = pd.DataFrame({
        "full_timestamp": timestamps,
        "kp_index": kp_index,
        "solar_flux_index_sfu": solar_flux_index
    })
    
    return full_weather_df


def generate_full_satellite_telemetry(full_weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Simulates continuous technical and operational satellite telemetry data,
    over a full 1440-period time series, with a subtle degradation
    directly linked to the specific space weather flare peak.
    """
    np.random.seed(42)
    periods = len(full_weather_df)
    timestamps = full_weather_df["full_timestamp"].values
    
    # 1. Base telemetry: smooth sinusoidal signals + normal noise + smoothing
    # Define a base sin wave cycle (e.g., 1 cycle per day). periods is 5 days. so 5 cycles.
    frequency = 5
    t_base = np.linspace(0, frequency * 2 * np.pi, periods)
    
    # Solar Current (typical 12A, subtle 1 cycle variation)
    solar_current_base = 12.0 + 1.0 * np.sin(t_base)
    solar_current_noisy = solar_current_base + np.random.normal(loc=0, scale=0.1, size=periods)
    solar_current_smooth = pd.Series(solar_current_noisy).rolling(window=12, min_periods=1).mean().values
    
    # Battery Temperature (typical 22°C, subtle 1 cycle variation)
    battery_temp_base = 22.0 + 2.0 * np.sin(t_base)
    battery_temp_noisy = battery_temp_base + np.random.normal(loc=0, scale=0.5, size=periods)
    battery_temp_smooth = pd.Series(battery_temp_noisy).rolling(window=12, min_periods=1).mean().values
    
    # Bus Voltage (typical 28V, smooth with minimal variation)
    bus_voltage_noisy = 28.0 + np.random.normal(loc=0, scale=0.05, size=periods)
    bus_voltage_smooth = pd.Series(bus_voltage_noisy).rolling(window=12, min_periods=1).mean().values
    
    # 2. Injected degradation response over the anomaly window
    anomaly_start_idx = int(periods * 0.75)
    anomaly_window_weather = full_weather_df.iloc[anomaly_start_idx:]
    
    # Identify the specific large-amplitude Kp peak in the anomaly window
    peak_weather_point = anomaly_window_weather.loc[anomaly_window_weather["kp_index"].idxmax()]
    peak_kp = peak_weather_point["kp_index"]
    peak_time = peak_weather_point["full_timestamp"]
    
    # Model degradation as a ramp-and-decay pulse (response function). max length 360 points (1.25 days).
    t_pulse_points = periods - anomaly_start_idx 
    t_rel = np.linspace(0, 1, t_pulse_points)
    
    # Model a smooth response pulse (ramp and slower decay). peak around 10% in (1 hour).
    t_peak_pulse = 0.1 # peak degradation is at 10% into window.
    sigma_impact = 0.2 # decay width
    pulse_impact = np.exp(-(t_rel - t_peak_pulse)**2 / (2 * sigma_impact**2))
    
    # The magnitude of degradation scales with the peak Kp value relative to average.
    avg_kp_base = full_weather_df.iloc[:anomaly_start_idx]["kp_index"].mean() # around 2.0
    
    # Scale: only start degradation for Kp > avg + 1. max scale to 1.0 for Kp around 9.
    kp_excess = np.maximum(0, peak_kp - avg_kp_base - 1) 
    kp_scale = np.minimum(1.0, kp_excess / 6.0) 
    
    # Maximum subtle subtle degradation amplitudes for a very large solar flare.
    max_impact_current_A = 1.5 * kp_scale # peak drop up to 1.5A
    max_impact_temp_C = 8.0 * kp_scale # peak increase up to 8°C
    max_impact_voltage_V = 0.7 * kp_scale # peak drop up to 0.7V
    
    # 3. Apply subtle degradation response pulse and combine
    solar_current = solar_current_smooth.copy()
    battery_temp = battery_temp_smooth.copy()
    bus_voltage = bus_voltage_smooth.copy()
    
    solar_current[anomaly_start_idx:] -= (max_impact_current_A * pulse_impact)
    battery_temp[anomaly_start_idx:] += (max_impact_temp_C * pulse_impact)
    bus_voltage[anomaly_start_idx:] -= (max_impact_voltage_V * pulse_impact)
    
    # Combine full time series
    full_telemetry_df = pd.DataFrame({
        "full_timestamp": timestamps,
        "solar_panel_current_A": solar_current,
        "battery_temperature_C": battery_temp,
        "bus_voltage_V": bus_voltage
    })
    
    return full_telemetry_df


def save_telemetry_plots(df: pd.DataFrame, output_path: str):
    """
    Generates exploratory data analysis plots showing the continuous telemetry,
    environmental variables, and the corresponding space weather anomaly window.
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # Plot 1: Solar Panel Current
    axes[0].plot(df["timestamp"], df["solar_panel_current_A"], color="tab:blue", label="Solar Panel Current (A)")
    axes[0].set_ylabel("Current (A)")
    axes[0].set_title("Continuous Satellite Telemetry & Linked Space Weather Correlation (Project ASTRA)", fontsize=14, fontweight='bold')
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

    # Draw a vertical dashed line at the designated anomaly start point (timestamp ~ 2026-07-04 18:00)
    anomaly_start_idx = int(len(df) * 0.75)
    anomaly_time = df["timestamp"].iloc[anomaly_start_idx]
    
    for ax in axes:
        ax.axvline(x=anomaly_time, color="darkred", linestyle=":", linewidth=2.5)
        if ax == axes[0]:
            ax.text(anomaly_time, ax.get_ylim()[1] * 0.85, ' Designated Anomaly Window', color='darkred', fontweight='bold', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"📊 EDA visualizations successfully saved to: {output_path}")


def main():
    print("🛰️ Starting Continuous Data Ingestion Pipeline for Project ASTRA...")
    start_date = datetime(2026, 7, 1, 0, 0, 0)
    periods = 1440 # 5 days in 5-minute intervals
    
    # 1. Generate full continuous time series data
    print("☀️ Generating full continuous Environmental Space Weather time series...")
    full_weather_df = generate_full_space_weather_data(start_date, periods)
    
    print("📊 Generating full Continuous Satellite Telemetry time series, linked to weather peak...")
    full_telemetry_df = generate_full_satellite_telemetry(full_weather_df)
    
    # 2. Make data interoperable (Downsampling and Merging)
    print("🔄 Making heterogeneous datasets interoperable (downsampling and alignment)...")
    
    # Resample space weather (downsample from 5 min to 15 min by taking every 3rd point)
    env_weather_df = full_weather_df.iloc[::3].copy()
    env_weather_df = env_weather_df.rename(columns={"full_timestamp": "env_timestamp"})
    
    # Pre-process for merge_asof: Sort. They are already sorted. Direction "backward" will align nearest 15-min weather point.
    
    unified_dataset = pd.merge_asof(
        full_telemetry_df.rename(columns={"full_timestamp": "timestamp"}), # standard timestamp
        env_weather_df,
        left_on="timestamp",
        right_on="env_timestamp",
        direction="backward"
    )
    # Drop duplicate env_timestamp
    unified_dataset = unified_dataset.drop(columns=["env_timestamp"]).ffill().bfill()
    
    # 3. Save CSV and Plot Artifacts to data/raw
    os.makedirs("data/raw", exist_ok=True)
    
    csv_output_path = "data/raw/telemetry_space_weather.csv"
    unified_dataset.to_csv(csv_output_path, index=False)
    print(f"✅ AI-ready continuous dataset saved to: {csv_output_path}")
    
    plot_output_path = "data/raw/telemetry_anomaly_plot.png"
    save_telemetry_plots(unified_dataset, plot_output_path)
    
    print(f"📊 Total Records Processed: {len(unified_dataset)}")


if __name__ == "__main__":
    main()
