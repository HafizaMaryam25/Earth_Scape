"""
EarthScape Climate Agency - Master ML Evaluation & Diagnostics Pipeline
Loads saved model artifacts, evaluates performance against benchmark metrics,
generates residual distributions, and prints detailed diagnostic reports.
"""

from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd

from src.data.ingestion import ClimateDataIngestionPipeline
from src.ml.forecast_model import get_chronological_split, evaluate_forecast_pipeline
from src.ml.anomaly_model import evaluate_anomaly_detection, predict_anomalies
from src.ml.impact_model import create_impact_dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "models"


def run_full_evaluation():
    """
    Executes rigorous evaluation across all serialized ML models.
    """
    print("=== Master ML Diagnostics & Evaluation Suite ===")
    ingestion = ClimateDataIngestionPipeline()
    df_climate = ingestion.load_historical_data()
    df_ghg = ingestion.load_greenhouse_gas_data()

    report = {}

    # 1. Evaluate Temperature Forecaster
    forecast_path = MODEL_DIR / "temp_forecaster.joblib"
    if forecast_path.exists():
        print("\n[1] Evaluating Saved Forecaster Model Artifact...")
        model_forecast = joblib.load(forecast_path)
        X_train, X_test, y_train, y_test = get_chronological_split(df_climate, split_year=2023)
        metrics_forecast = evaluate_forecast_pipeline(model_forecast, X_test, y_test)
        
        preds = model_forecast.predict(X_test)
        residuals = y_test.values - preds
        
        report["forecaster"] = {
            "metrics": metrics_forecast,
            "residual_mean": round(float(np.mean(residuals)), 4),
            "residual_std": round(float(np.std(residuals)), 4),
            "test_sample_count": len(y_test)
        }
        print(f"  RMSE: {metrics_forecast['rmse']}°C | MAE: {metrics_forecast['mae']}°C | R2: {metrics_forecast['r2_score']}")
    else:
        print("  [!] Forecaster artifact missing. Run train_all.py first.")

    # 2. Evaluate Anomaly Detector
    anomaly_path = MODEL_DIR / "anomaly_detector.joblib"
    if anomaly_path.exists():
        print("\n[2] Evaluating Saved Anomaly Detector Artifact...")
        model_anomaly = joblib.load(anomaly_path)
        metrics_anomaly = evaluate_anomaly_detection(model_anomaly, df_climate)
        report["anomaly_detector"] = metrics_anomaly
        print(f"  F1: {metrics_anomaly['f1_score']} | Precision: {metrics_anomaly['precision']} | Recall: {metrics_anomaly['recall']}")
        print(f"  Confusion Matrix: {metrics_anomaly['confusion_matrix']}")
    else:
        print("  [!] Anomaly detector artifact missing.")

    # 3. Evaluate Impact Model
    impact_path = MODEL_DIR / "impact_model.joblib"
    if impact_path.exists():
        print("\n[3] Evaluating Saved Impact Regressor Artifact...")
        model_impact = joblib.load(impact_path)
        X_impact, y_impact = create_impact_dataset(df_ghg)
        preds_impact = model_impact.predict(X_impact)
        
        from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
        r2 = r2_score(y_impact, preds_impact)
        rmse = np.sqrt(mean_squared_error(y_impact, preds_impact))
        mae = mean_absolute_error(y_impact, preds_impact)
        
        report["impact_regressor"] = {
            "r2_score": round(float(r2), 4),
            "rmse": round(float(rmse), 4),
            "mae": round(float(mae), 4)
        }
        print(f"  R2: {round(float(r2), 4)} | RMSE: {round(float(rmse), 4)} | MAE: {round(float(mae), 4)}")

    report_path = MODEL_DIR / "evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n[+] Full evaluation report saved to {report_path.name}")

    return report


if __name__ == "__main__":
    run_full_evaluation()
