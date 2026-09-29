"""
EarthScape Climate Agency - Machine Learning Model 2: Climate Anomaly & Extreme Event Detector
Implements an unsupervised Isolation Forest model for multi-dimensional anomaly detection
across temperature, pressure drop, wind gusts, humidity, and atmospheric greenhouse spikes.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


ANOMALY_FEATURE_COLS = [
    "surface_temp_c",
    "precipitation_mm",
    "humidity_pct",
    "pressure_hpa",
    "wind_speed_kmh",
    "solar_irradiance_wm2",
    "co2_ppm",
    "aerosol_optical_depth"
]


def build_anomaly_pipeline(contamination: float = 0.05, random_state: int = 42) -> Pipeline:
    """
    Builds a robust scaling + Isolation Forest anomaly detection pipeline.
    """
    pipeline = Pipeline([
        ("scaler", RobustScaler()),
        ("detector", IsolationForest(
            n_estimators=150,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1
        ))
    ])
    return pipeline


def train_anomaly_model(df: pd.DataFrame, contamination: float = 0.05) -> Pipeline:
    """
    Trains the Isolation Forest model on historical multi-variate observations.
    """
    X = df[ANOMALY_FEATURE_COLS].copy()
    pipeline = build_anomaly_pipeline(contamination=contamination)
    pipeline.fit(X)
    return pipeline


def predict_anomalies(pipeline: Pipeline, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Scores records.
    Returns:
    - is_anomaly: 1 if anomaly, 0 if normal.
    - anomaly_scores: Higher score = more anomalous.
    """
    X = df[ANOMALY_FEATURE_COLS].copy()
    # IsolationForest outputs -1 for anomaly and 1 for normal
    raw_preds = pipeline.predict(X)
    is_anomaly = np.where(raw_preds == -1, 1, 0)
    
    # Decision function: lower values mean more anomalous; we invert so higher is more anomalous
    detector = pipeline.named_steps["detector"]
    scaler = pipeline.named_steps["scaler"]
    X_scaled = scaler.transform(X)
    raw_scores = detector.decision_function(X_scaled)
    # Normalize score to 0-100 anomaly intensity index
    norm_scores = np.clip((0.25 - raw_scores) * 200.0, 0.0, 100.0)

    return is_anomaly, np.round(norm_scores, 2)


def evaluate_anomaly_detection(pipeline: Pipeline, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates unsupervised anomaly detector against synthetic ground truth extreme tags.
    """
    is_anomaly, scores = predict_anomalies(pipeline, df)
    ground_truth = np.where(df["extreme_event_tag"] != "NORMAL", 1, 0)

    prec = precision_score(ground_truth, is_anomaly, zero_division=0)
    rec = recall_score(ground_truth, is_anomaly, zero_division=0)
    f1 = f1_score(ground_truth, is_anomaly, zero_division=0)
    cm = confusion_matrix(ground_truth, is_anomaly).tolist()

    return {
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "total_anomalies_flagged": int(np.sum(is_anomaly)),
        "anomaly_rate_pct": round(float(np.mean(is_anomaly)) * 100.0, 2),
        "confusion_matrix": cm,
        "mean_anomaly_score": round(float(np.mean(scores)), 2),
        "max_anomaly_score": round(float(np.max(scores)), 2)
    }
