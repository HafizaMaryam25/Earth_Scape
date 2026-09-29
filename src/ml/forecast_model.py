

from pathlib import Path
from typing import Tuple, Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def engineer_climate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates temporal, seasonal, harmonic, and lag features for climate time series.
    """
    data = df.copy()
    if not np.issubdtype(data["timestamp"].dtype, np.datetime64):
        data["timestamp"] = pd.to_datetime(data["timestamp"])

    data = data.sort_values(by=["zone_id", "timestamp"]).reset_index(drop=True)

    # Cyclical day-of-year encoding
    day_of_year = data["timestamp"].dt.dayofyear
    data["sin_day"] = np.sin(2 * np.pi * day_of_year / 365.25)
    data["cos_day"] = np.cos(2 * np.pi * day_of_year / 365.25)

    # Temporal index
    min_year = data["year"].min()
    data["trend_index"] = (data["year"] - min_year) + (day_of_year / 365.25)

    # Rolling lag features per zone (7-day and 30-day moving averages)
    data["temp_lag_7d"] = data.groupby("zone_id")["surface_temp_c"].shift(7)
    data["temp_lag_30d"] = data.groupby("zone_id")["surface_temp_c"].shift(30)
    data["temp_rolling_mean_30d"] = data.groupby("zone_id")["surface_temp_c"].transform(
        lambda s: s.rolling(window=30, min_periods=1).mean()
    )

    # Fill NA from shifting with the zone baseline
    data["temp_lag_7d"] = data["temp_lag_7d"].fillna(data["surface_temp_c"])
    data["temp_lag_30d"] = data["temp_lag_30d"].fillna(data["surface_temp_c"])

    return data


def get_chronological_split(
    df: pd.DataFrame, split_year: int = 2023
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Strict chronological split: Training on data <= split_year, Testing on data > split_year.
    Avoids data leakage in time-series forecasting.
    """
    fe_df = engineer_climate_features(df)

    feature_cols = [
        "zone_id", "trend_index", "sin_day", "cos_day",
        "co2_ppm", "ch4_ppb", "solar_irradiance_wm2",
        "humidity_pct", "pressure_hpa", "aerosol_optical_depth",
        "temp_lag_7d", "temp_lag_30d", "temp_rolling_mean_30d"
    ]
    target_col = "surface_temp_c"

    train_mask = fe_df["year"] <= split_year
    test_mask = fe_df["year"] > split_year

    X_train = fe_df.loc[train_mask, feature_cols]
    y_train = fe_df.loc[train_mask, target_col]
    X_test = fe_df.loc[test_mask, feature_cols]
    y_test = fe_df.loc[test_mask, target_col]

    return X_train, X_test, y_train, y_test


def build_forecasting_pipeline(model_type: str = "gradient_boosting", random_state: int = 42) -> Pipeline:
    """
    Builds an end-to-end preprocessing and regression pipeline.
    """
    categorical_features = ["zone_id"]
    numeric_features = [
        "trend_index", "sin_day", "cos_day", "co2_ppm", "ch4_ppb",
        "solar_irradiance_wm2", "humidity_pct", "pressure_hpa",
        "aerosol_optical_depth", "temp_lag_7d", "temp_lag_30d", "temp_rolling_mean_30d"
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ]
    )

    if model_type == "gradient_boosting":
        regressor = GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=5,
            random_state=random_state
        )
    elif model_type == "random_forest":
        regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            random_state=random_state,
            n_jobs=-1
        )
    else:
        raise ValueError(f"Unsupported model_type: {model_type}")

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", regressor)
    ])

    return pipeline


def evaluate_forecast_pipeline(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Computes regression evaluation metrics: RMSE, MAE, R2 score.
    """
    preds = pipeline.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    return {
        "rmse": round(float(rmse), 4),
        "mae": round(float(mae), 4),
        "r2_score": round(float(r2), 4)
    }
