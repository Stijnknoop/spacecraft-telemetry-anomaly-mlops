# Standard library imports
import json
import os

# Third-party library imports
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import IsolationForest


def load_data(filepath: str) -> pd.DataFrame:
    """Loads the ingested spacecraft telemetry dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Target data file not found at {filepath}. Run data ingestion first.")
    df = pd.read_csv(filepath)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def train_anomaly_detector(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trains an unsupervised Isolation Forest model on multi-domain features
    to isolate and detect operational and environmental anomalies.
    """
    print("🤖 Training Isolation Forest anomaly detection model...")
    
    features = [
        "solar_panel_current_A", 
        "battery_temperature_C", 
        "bus_voltage_V", 
        "kp_index", 
        "solar_flux_index_sfu"
    ]
    
    X = df[features]
    
    # Estimate contamination around 25% based on our known simulation window
    model = IsolationForest(contamination=0.25, random_state=42)
    model.fit(X)
    
    predictions = model.predict(X)
    df["anomaly_predicted"] = [1 if pred == -1 else 0 for pred in predictions]
    df["anomaly_score"] = model.decision_function(X)
    
    return df


def generate_ml_artifacts(df: pd.DataFrame, plot_path: str, json_path: str):
    """
    Generates multi-plot model evaluation visualizations and structures metadata.
    Filters out transient noise to find the true sustained anomaly window.
    """
    # --- Artifact 1: Professional 3-Subplot ML Visualization ---
    print(f"📊 Generating 3-subplot ML evaluation plot at: {plot_path}")
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    anomalies = df[df["anomaly_predicted"] == 1]

    # Subplot 1: Solar Panel Current with ML Anomalies
    axes[0].plot(df["timestamp"], df["solar_panel_current_A"], color="tab:blue", alpha=0.6, label="Solar Panel Current (A)")
    axes[0].scatter(anomalies["timestamp"], anomalies["solar_panel_current_A"], color="red", s=10, label="Detected Anomaly (ML)", zorder=3)
    axes[0].set_ylabel("Current (A)")
    axes[0].set_title("Spacecraft Anomaly Detection Output (scikit-learn Isolation Forest)", fontsize=14, fontweight="bold")
    axes[0].grid(True, linestyle="--", alpha=0.5)
    axes[0].legend(loc="upper left")

    # Subplot 2: Battery Temperature with ML Anomalies
    axes[1].plot(df["timestamp"], df["battery_temperature_C"], color="tab:red", alpha=0.6, label="Battery Temp (°C)")
    axes[1].scatter(anomalies["timestamp"], anomalies["battery_temperature_C"], color="red", s=10, label="Detected Anomaly (ML)", zorder=3)
    axes[1].set_ylabel("Temperature (°C)")
    axes[1].grid(True, linestyle="--", alpha=0.5)
    axes[1].legend(loc="upper left")

    # Subplot 3: Kp Index with ML Anomalies
    axes[2].plot(df["timestamp"], df["kp_index"], color="tab:orange", alpha=0.6, label="Space Weather Kp Index")
    axes[2].scatter(anomalies["timestamp"], anomalies["kp_index"], color="red", s=10, label="Detected Anomaly (ML)", zorder=3)
    axes[2].set_ylabel("Kp Index")
    axes[2].set_xlabel("Timestamp")
    axes[2].grid(True, linestyle="--", alpha=0.5)
    axes[2].legend(loc="upper left")

    # Highlight the designated anomaly threshold line
    anomaly_start_idx = int(len(df) * 0.75)
    anomaly_time = df["timestamp"].iloc[anomaly_start_idx]
    for ax in axes:
        ax.axvline(x=anomaly_time, color="darkred", linestyle=":", linewidth=2)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    
    # --- Artifact 2: Robust JSON Metadata for LLM Agents ---
    print(f"💾 Generating clean JSON metadata digest at: {json_path}")
    
    df['block'] = (df['anomaly_predicted'] != df['anomaly_predicted'].shift()).cumsum()
    block_sizes = df.groupby('block')['anomaly_predicted'].transform('size')
    sustained_anomalies = df[(df['anomaly_predicted'] == 1) & (block_sizes >= 6)]
    
    if not sustained_anomalies.empty:
        metadata = {
            "analysis_status": "CRITICAL_ANOMALY_DETECTED",
            "total_records_analyzed": len(df),
            "anomaly_points_count": int(len(anomalies)),
            "anomaly_start_time": str(sustained_anomalies["timestamp"].min()),
            "anomaly_end_time": str(sustained_anomalies["timestamp"].max()),
            "max_observed_kp_index": float(sustained_anomalies["kp_index"].max()),
            "max_battery_temperature_C": float(sustained_anomalies["battery_temperature_C"].max()),
            "min_solar_current_A": float(sustained_anomalies["solar_panel_current_A"].min()),
            "model_confidence_average": float(abs(sustained_anomalies["anomaly_score"].mean()))
        }
    else:
        metadata = {
            "analysis_status": "NOMINAL",
            "total_records_analyzed": len(df),
            "anomaly_points_count": int(len(anomalies))
        }
        
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=4)


def main():
    print("🚀 Starting Machine Learning Pipeline...")
    input_csv = "data/raw/telemetry_space_weather.csv"
    output_csv = "data/processed/telemetry_processed.csv"
    output_plot = "data/processed/ml_anomalies_detected.png"
    output_json = "data/processed/anomaly_digest.json"
    
    os.makedirs("data/processed", exist_ok=True)
    
    df = load_data(input_csv)
    df_analyzed = train_anomaly_detector(df)
    df_analyzed.to_csv(output_csv, index=False)
    generate_ml_artifacts(df_analyzed, output_plot, output_json)
    print("🏁 Machine Learning Pipeline execution finished successfully.")


if __name__ == "__main__":
    main()
