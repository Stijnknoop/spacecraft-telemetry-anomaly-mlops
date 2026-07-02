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
    
    # We estimate contamination around 25% based on our known simulation window
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
    Generates and saves model evaluation plots and structured metadata 
    for downstream consumption by AI agents.
    """
    # --- Artifact 1: Visualization ---
    print(f"📊 Generating ML evaluation plot at: {plot_path}")
    plt.figure(figsize=(12, 6))
    
    # Plot battery temperature as the reference timeline
    plt.plot(df["timestamp"], df["battery_temperature_C"], color="gray", alpha=0.6, label="Battery Temp (°C)")
    
    # Overlay detected anomalies
    anomalies = df[df["anomaly_predicted"] == 1]
    plt.scatter(anomalies["timestamp"], anomalies["battery_temperature_C"], color="red", s=15, label="Detected Anomaly (ML)")
    
    plt.title("Spacecraft Anomaly Detection Output (scikit-learn Isolation Forest)", fontsize=14, fontweight="bold")
    plt.xlabel("Timestamp")
    plt.ylabel("Telemetry Value")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper left")
    
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    
    # --- Artifact 2: JSON Metadata for LLM Agents ---
    print(f"💾 Generating JSON metadata digest for GenAI layer at: {json_path}")
    
    anomaly_window = df[df["anomaly_predicted"] == 1]
    
    if not anomaly_window.empty:
        metadata = {
            "analysis_status": "CRITICAL_ANOMALY_DETECTED",
            "total_records_analyzed": len(df),
            "anomaly_points_count": int(len(anomaly_window)),
            "anomaly_start_time": str(anomaly_window["timestamp"].min()),
            "anomaly_end_time": str(anomaly_window["timestamp"].max()),
            "max_observed_kp_index": float(anomaly_window["kp_index"].max()),
            "max_battery_temperature_C": float(anomaly_window["battery_temperature_C"].max()),
            "min_solar_current_A": float(anomaly_window["solar_panel_current_A"].min()),
            "model_confidence_average": float(abs(anomaly_window["anomaly_score"].mean()))
        }
    else:
        metadata = {
            "analysis_status": "NOMINAL",
            "total_records_analyzed": len(df),
            "anomaly_points_count": 0
        }
        
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=4)

def main():
    print("🚀 Starting Machine Learning Pipeline for Project ASTRA...")
    
    input_csv = "data/telemetry_space_weather.csv"
    output_csv = "data/telemetry_processed.csv"
    output_plot = "data/ml_anomalies_detected.png"
    output_json = "data/anomaly_digest.json"
    
    # 1. Load data
    df = load_data(input_csv)
    
    # 2. Run unsupervised anomaly detection
    df_analyzed = train_anomaly_detector(df)
    
    # 3. Save processed dataset
    df_analyzed.to_csv(output_csv, index=False)
    print(f"✅ Processed dataset with ML labels saved to: {output_csv}")
    
    # 4. Export plots and JSON digests
    generate_ml_artifacts(df_analyzed, output_plot, output_json)
    print("🏁 Machine Learning Pipeline execution finished successfully.")

if __name__ == "__main__":
    main()
