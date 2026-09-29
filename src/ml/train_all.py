"""
EarthScape Climate Agency - Master ML Training Pipeline
Trains all 3 climate ML models, computes validation metrics, and serializes artifacts into models/
"""

import sys
from pathlib import Path
import json
import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
for p in [str(PROJECT_ROOT), str(SRC_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from src.data.ingestion import ClimateDataIngestionPipeline
    from src.ml.forecast_model import (
        get_chronological_split,
        build_forecasting_pipeline,
        evaluate_forecast_pipeline
    )
    from src.ml.anomaly_model import (
        train_anomaly_model,
        evaluate_anomaly_detection
    )
    from src.ml.impact_model import (
        train_impact_model
    )
except ImportError:
    from data.ingestion import ClimateDataIngestionPipeline
    from ml.forecast_model import (
        get_chronological_split,
        build_forecasting_pipeline,
        evaluate_forecast_pipeline
    )
    from ml.anomaly_model import (
        train_anomaly_model,
        evaluate_anomaly_detection
    )
    from ml.impact_model import (
        train_impact_model
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def train_and_export_all_models():
    """
    Executes end-to-end training of all three models and persists artifacts.
    """
    print("=== EarthScape Climate Machine Learning Training Suite ===")
    ingestion = ClimateDataIngestionPipeline()
    df_climate = ingestion.load_historical_data()
    df_ghg = ingestion.load_greenhouse_gas_data()

    # -------------------------------------------------------------
    # 1. Model 1: Climate Trend & Temperature Forecaster
    # -------------------------------------------------------------
    print("\n[1/3] Training Climate Trend & Temperature Forecaster...")
    X_train, X_test, y_train, y_test = get_chronological_split(df_climate, split_year=2023)
    print(f"  - Chronological Split: Train (<=2023) = {len(X_train)} samples, Test (>2023) = {len(X_test)} samples")
    
    forecast_pipeline = build_forecasting_pipeline(model_type="gradient_boosting")
    forecast_pipeline.fit(X_train, y_train)
    forecast_metrics = evaluate_forecast_pipeline(forecast_pipeline, X_test, y_test)
    print(f"  - Forecaster Test Metrics: R2={forecast_metrics['r2_score']:.4f}, RMSE={forecast_metrics['rmse']:.3f}°C, MAE={forecast_metrics['mae']:.3f}°C")

    forecast_model_path = MODEL_DIR / "temp_forecaster.joblib"
    joblib.dump(forecast_pipeline, forecast_model_path)
    print(f"  [+] Saved forecaster artifact to {forecast_model_path.name}")

    # -------------------------------------------------------------
    # 2. Model 2: Climate Anomaly & Extreme Event Detector
    # -------------------------------------------------------------
    print("\n[2/3] Training Climate Anomaly & Extreme Event Detector (Isolation Forest)...")
    anomaly_pipeline = train_anomaly_model(df_climate, contamination=0.06)
    anomaly_metrics = evaluate_anomaly_detection(anomaly_pipeline, df_climate)
    print(f"  - Anomaly Detector: F1-Score={anomaly_metrics['f1_score']:.4f}, Precision={anomaly_metrics['precision']:.4f}, Recall={anomaly_metrics['recall']:.4f}")
    print(f"  - Total Anomalies Flagged: {anomaly_metrics['total_anomalies_flagged']} ({anomaly_metrics['anomaly_rate_pct']}%)")

    anomaly_model_path = MODEL_DIR / "anomaly_detector.joblib"
    joblib.dump(anomaly_pipeline, anomaly_model_path)
    print(f"  [+] Saved anomaly detector artifact to {anomaly_model_path.name}")

    # -------------------------------------------------------------
    # 3. Model 3: Climate Impact & Risk Regressor
    # -------------------------------------------------------------
    print("\n[3/3] Training Climate Impact & Risk Regressor...")
    impact_pipeline, impact_metrics = train_impact_model(df_ghg)
    print(f"  - Impact Model Metrics: R2={impact_metrics['r2_score']:.4f}, RMSE={impact_metrics['rmse']:.3f}, MAE={impact_metrics['mae']:.3f}")

    impact_model_path = MODEL_DIR / "impact_model.joblib"
    joblib.dump(impact_pipeline, impact_model_path)
    print(f"  [+] Saved impact model artifact to {impact_model_path.name}")

    # -------------------------------------------------------------
    # Consolidate Training Metadata
    # -------------------------------------------------------------
    master_metrics = {
        "temperature_forecaster": {
            "model_type": "GradientBoostingRegressor",
            "split_strategy": "Chronological (Train: 2015-2023, Test: 2024-2025)",
            "metrics": forecast_metrics,
            "artifact": str(forecast_model_path.name)
        },
        "anomaly_detector": {
            "model_type": "IsolationForest + RobustScaler",
            "contamination": 0.06,
            "metrics": anomaly_metrics,
            "artifact": str(anomaly_model_path.name)
        },
        "impact_regressor": {
            "model_type": "RandomForestRegressor",
            "target": "Climate Vulnerability Risk Index (0-100)",
            "metrics": impact_metrics,
            "artifact": str(impact_model_path.name)
        }
    }

    metrics_file = MODEL_DIR / "models_evaluation_summary.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(master_metrics, f, indent=2)
    print(f"\n[+] Master model summary written to {metrics_file}")
    print("All ML models trained and serialized successfully!")

    return master_metrics


if __name__ == "__main__":
    train_and_export_all_models()
