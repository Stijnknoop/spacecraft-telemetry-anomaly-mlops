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
    
    # Select numerical features for the model (combining technical and environmental domains)
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
    
    # Isolation Forest outputs -1 for anomalies and 1 for normal data
    predictions = model.predict(X)
    
    # Map to standard binary classification: 1 for anomaly, 0 for normal
    df["anomaly_predicted"] = [1 if pred == -1 else 0 for pred in predictions]
    
    # Extract anomaly scores (lower scores mean more anomalous)
    df["anomaly_score"] = model.decision_function(X)
    
    return df


def generate_ml_artifacts(df: pd.DataFrame, plot_path: str, json_path: str):
    """
    Generates model evaluation plots and structures metadata.
    Filters out transient noise to find the true sustained anomaly window.
    """
    # --- Artifact 1: Visualization ---
    print(f"📊 Generating ML evaluation plot at: {plot_path}")
    plt.figure(figsize=(12, 6))
    plt.plot(df["timestamp"], df["battery_temperature_C"], color="gray", alpha=0.6, label="Battery Temp (°C)")
    
    anomalies = df[df["anomaly_predicted"] == 1]
    plt.scatter(anomalies["timestamp"], anomalies["battery_temperature_C"], color="red", s=15, label="Detected Anomaly (ML)")
    plt.title("Spacecraft Anomaly Detection Output (scikit-learn Isolation Forest)", fontsize=14, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    
    # --- Artifact 2: Robust JSON Metadata for LLM Agents ---
    print(f"💾 Generating clean JSON metadata digest at: {json_path}")
    
    # Signal Processing: Identify continuous blocks to filter out isolated noise points
    df['block'] = (df['anomaly_predicted'] != df['anomaly_predicted'].shift()).cumsum()
    block_sizes = df.groupby('block')['anomaly_predicted'].transform('size')
    
    # Filter for anomalies that persist for at least 6 consecutive periods (30 minutes)
    sustained_anomalies = df[(df['anomaly_predicted'] == 1) & (block_sizes >= 6)]
    
    if not sustained_anomalies.empty:
        metadata = {
            "analysis_status": "CRITICAL_ANOMALY_DETECTED",
            "total_records_analyzed": len(df),
            "anomaly_points_count": int(len(anomalies)),
            "anomaly_start_time": str(sustained_anomalies["timestamp"].min()),  # Pure window start
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
