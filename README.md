# 🛰️ Project ASTRA: Spacecraft Telemetry Anomaly Detection & Multi-Agent MLOps Pipeline

This project is an automated, end-to-end MLOps and GenAI pipeline designed for **ESA (European Space Agency)** mission control scenarios. The core objective of Project ASTRA is to demonstrate that cross-domain correlations between external space weather and internal satellite telemetry can be automatically detected, analyzed, and translated into strategic emergency operations briefs for agency executives.

---

## 🌌 1. What Are We Investigating?

In space operations, satellites operate in an incredibly hostile environment. Traditional monitoring systems often rely on static 'out-of-bounds' thresholds for individual sensors (e.g., checking if a single temperature reading is too high). Project ASTRA explores a far more advanced methodology: **unsupervised multi-domain anomaly detection**.

We correlate two distinct data domains:
1. **External Environmental Domain (Space Weather via NOAA standards):** The *Kp-index* (geomagnetic storm intensity ranging from 0-9) and the *Solar Flux Index (SFU)*.
2. **Internal Technical Subsystem Domain (Satellite Telemetry):** The generated current from solar arrays (Solar Panel Current in Amps), the internal battery temperature (Battery Temperature in °C), and the main voltage line (Bus Voltage in Volts).

### The Injected Crisis Scenario
When a severe solar storm (Solar Flare) impacts the spacecraft, it triggers a subtle, interconnected chain reaction: solar panels temporarily degrade due to high-energy particle bombardment (current drop), the spacecraft experiences minor attitude perturbations due to atmospheric compression, and the battery runs warmer due to a disrupted power equilibrium. The ML algorithm must recognize this multi-domain signature *even if individual metrics remain just within their independent safe operating limits*.

---

## 🏗️ 2. Pipeline Architecture & Data Flow

The system is engineered as a three-tier modular pipeline, moving seamlessly from raw environmental physics to executive decision-making.

### 🔁 Layer 1: DataOps (Continuous Ingestion & Interoperability)
To replicate flight-like telemetry environments, this layer generates a mathematically smooth, continuous time series consisting of 1,440 data points (representing 5 days of operations at 5-minute intervals). Instead of flat lines, the data features realistic noise and diurnal sinusoidal variations (representing the satellite's orbital day/night cycles). 

The environmental data (NOAA-style) and onboard telemetry are generated at differing frequencies, utilizing a high-performance `pd.merge_asof` temporal alignment (backward matching) to fuse these heterogeneous sources into a single, AI-ready dataset (`data/raw/telemetry_space_weather.csv`).

### 🤖 Layer 2: MLOps (Unsupervised Machine Learning)
An unsupervised **Isolation Forest** model from `scikit-learn` is trained on the combined feature space. Because space asset failures are rare, the model learns to isolate tight, normal operational clusters from abnormal multi-variate outliers. 

To prevent point-anomaly 'noise' (such as isolated flags on nominal days), a custom signal processing filter detects a *sustained anomaly window* (a minimum of 30 consecutive minutes of anomaly flags). This eliminates transient noise and isolates the exact onset timestamp of the space weather impact, exporting a concise **`anomaly_digest.json`** packed with critical metrics.

### 👥 Layer 3: GenAI Layer (Multi-Agent Conversational Orchestration)
Large Language Models (LLMs) parse massive, raw CSV files poorly in production environments. Instead, this layer ingests the dense `anomaly_digest.json`. We leverage **CrewAI** to orchestrate a hierarchical team of three specialized AI agents powered by **Gemini 2.5 Flash**:
* **Senior Telemetry Analyst:** Extracts raw telemetry vectors from the JSON (timestamps, peak temperatures, current minimums) and compiles a clean technical status table.
* **Explainable AI (XAI) Expert:** Ensures mission safety and system transparency by explaining *why* the Isolation Forest flag was raised, highlighting cross-domain physics correlations, and interpreting average model confidence scores.
* **ESA Operations & Management Advisor:** Synthesizes upstream technical context, formulates immediate contingency procedures, and calculates downstream impacts on Agency-level KPIs like the **Mission Availability Rate**, saving the final brief to `data/results/emergency_operations_brief.md`.
