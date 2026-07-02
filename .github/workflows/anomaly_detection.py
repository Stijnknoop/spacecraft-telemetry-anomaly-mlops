name: Spacecraft ML Processing

on:
  workflow_run:
    workflows: ["Spacecraft Data Ingestion"]
    types:
      - completed
  workflow_dispatch: # Allows manual trigger for testing

permissions:
  contents: write

jobs:
  train-and-evaluate:
    runs-on: ubuntu-latest
    # Only run if the data ingestion workflow succeeded, or if manually triggered
    if: ${{ github.event.workflow_run.conclusion == 'success' || github.event_name == 'workflow_dispatch' }}

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Cache pip dependencies
      uses: actions/cache@v4
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-v2-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

    - name: Run ML Anomaly Detection Model
      run: |
        python src/anomaly_detection.py

    - name: Commit and push ML artifacts
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        
        if [ -f data/telemetry_processed.csv ]; then
          git add data/telemetry_processed.csv data/ml_anomalies_detected.png data/anomaly_digest.json
          
          if git diff --quiet && git diff --staged --quiet; then
            echo "No changes detected in ML artifacts."
          else
            git commit -m "MLOps: Executed Isolation Forest and generated data digests"
            git pull --rebase origin main
            git push
          fi
        fi
