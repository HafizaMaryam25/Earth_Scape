"""
EarthScape Climate Agency - Machine Learning Model 3: Climate Impact & Risk Regressor
Predicts climate vulnerability risk index (0-100) based on greenhouse gas concentrations,
deforestation rates, aerosol depth, and sea surface temperature anomalies.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

IMPACT_FEATURES = [
    "co2_ppm",
    "ch4_ppb",
    "global_deforestation_rate_mha",
    "fossil_fuel_emissions_gtco2",
    "arctic_sea_ice_extent_mkm2"
]


def create_impact_dataset(ghg_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Constructs target climate risk index from empirical multi-factor warming variables.
    """
    df = ghg_df.copy()
    
    # Composite empirical Climate Vulnerability Risk Target (0 - 100)
    co2_factor = (df["co2_ppm"] - 365.0) * 0.75
    ch4_factor = (df["ch4_ppb"] - 1750.0) * 0.12
    ice_factor = (7.0 - df["arctic_sea_ice_extent_mkm2"]) * 6.5
    emissions_factor = df["fossil_fuel_emissions_gtco2"] * 0.85
    deforest_factor = df["global_deforestation_rate_mha"] * 1.8

    risk_score = 15.0 + co2_factor + ch4_factor + ice_factor + emissions_factor + deforest_factor
    risk_score = np.clip(risk_score + np.random.normal(0, 1.5, size=len(df)), 5.0, 100.0)
    
    df["climate_risk_index"] = np.round(risk_score, 2)
    
    X = df[IMPACT_FEATURES]
    y = df["climate_risk_index"]
    return X, y


def build_impact_pipeline(random_state: int = 42) -> Pipeline:
    """
    Creates Random Forest regression pipeline for climate risk index prediction.
    """
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("regressor", RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=random_state
        ))
    ])
    return pipeline


def train_impact_model(ghg_df: pd.DataFrame) -> Tuple[Pipeline, Dict[str, float]]:
    """
    Trains and validates the impact regression pipeline.
    """
    X, y = create_impact_dataset(ghg_df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = build_impact_pipeline()
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mae = float(mean_absolute_error(y_test, preds))
    r2 = float(r2_score(y_test, preds))

    metrics = {
        "rmse": round(rmse, 3),
        "mae": round(mae, 3),
        "r2_score": round(r2, 4)
    }

    return pipeline, metrics
