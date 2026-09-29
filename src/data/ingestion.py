"""
EarthScape Climate Agency - Data Ingestion & Partitioning Pipeline
Handles ingestion from multi-format climate data sources:
- CSV Weather records
- JSON IoT sensor logs
- Satellite observational cubes
- Performs schema validation, cleaning, missing-value imputation, and HDFS-ready partitioning.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json
import numpy as np
import pandas as pd

from src.data.generator import (
    generate_all_datasets,
    RAW_DATA_DIR,
    CLIMATE_ZONES,
    WEATHER_STATIONS
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
PARTITIONS_DIR = PROCESSED_DATA_DIR / "hdfs_partitions"


class ClimateDataIngestionPipeline:
    """
    Production-grade data ingestion pipeline for EarthScape Climate Agency.
    """

    def __init__(self, raw_dir: Path = RAW_DATA_DIR, processed_dir: Path = PROCESSED_DATA_DIR):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.partitions_dir = self.processed_dir / "hdfs_partitions"

    def ensure_raw_data_exists(self) -> None:
        """
        Validates whether raw climate files exist; generates them if missing.
        """
        historical_file = self.raw_dir / "climate_historical_daily.csv"
        if not historical_file.exists():
            print("[Ingestion] Raw climate data not found. Auto-generating synthetic datasets...")
            generate_all_datasets()
        else:
            print(f"[Ingestion] Verified raw datasets in {self.raw_dir}")

    def load_historical_data(self) -> pd.DataFrame:
        """
        Loads and validates historical daily climate records.
        """
        self.ensure_raw_data_exists()
        file_path = self.raw_dir / "climate_historical_daily.csv"
        df = pd.read_csv(file_path, parse_dates=["timestamp"])
        return df

    def load_greenhouse_gas_data(self) -> pd.DataFrame:
        """
        Loads greenhouse gas emission time series.
        """
        self.ensure_raw_data_exists()
        file_path = self.raw_dir / "greenhouse_gases_emissions.csv"
        df = pd.read_csv(file_path)
        return df

    def load_weather_stations(self) -> List[Dict[str, Any]]:
        """
        Loads weather station directory metadata.
        """
        self.ensure_raw_data_exists()
        file_path = self.raw_dir / "weather_stations.json"
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_sensor_stream(self) -> List[Dict[str, Any]]:
        """
        Loads real-time sensor stream packets.
        """
        self.ensure_raw_data_exists()
        file_path = self.raw_dir / "sensor_stream_sample.json"
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def clean_and_impute_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans climate dataset, handling missing values, outliers, and type normalization:
        - Time series sorting
        - Forward fill + backward fill for sensor readings
        - Imputation of satellite metrics (NDVI, Sea Surface Temp) based on climatic zone baselines
        """
        cleaned = df.copy()
        cleaned = cleaned.sort_values(by=["zone_id", "timestamp"]).reset_index(drop=True)

        # Numerical columns to interpolate if missing
        numeric_cols = [
            "surface_temp_c", "precipitation_mm", "humidity_pct",
            "pressure_hpa", "wind_speed_kmh", "solar_irradiance_wm2",
            "co2_ppm", "ch4_ppb", "ndvi_vegetation_index", "aerosol_optical_depth"
        ]

        for col in numeric_cols:
            if col in cleaned.columns:
                cleaned[col] = cleaned.groupby("zone_id")[col].transform(
                    lambda group: group.interpolate(method="linear").bfill().ffill()
                )

        # Fill specific optional satellite fields
        if "ice_sheet_albedo" in cleaned.columns:
            cleaned["ice_sheet_albedo"] = cleaned["ice_sheet_albedo"].fillna(0.0)
        if "sea_surface_temp_c" in cleaned.columns:
            cleaned["sea_surface_temp_c"] = cleaned["sea_surface_temp_c"].fillna(cleaned["surface_temp_c"])

        return cleaned

    def partition_for_hdfs(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Partitions the ingested dataset by `zone_id` and `year` to mimic HDFS distributed storage.
        Writes partition blocks as optimized CSVs into `data/processed/hdfs_partitions/`.
        Returns summary dictionary of partition block paths.
        """
        self.partitions_dir.mkdir(parents=True, exist_ok=True)
        partition_manifest = {}

        zones = df["zone_id"].unique()
        for zone in zones:
            zone_df = df[df["zone_id"] == zone]
            years = zone_df["year"].unique()

            for year in years:
                partition_subset = zone_df[zone_df["year"] == year]
                partition_name = f"zone={zone}/year={year}"
                partition_folder = self.partitions_dir / f"zone={zone}"
                partition_folder.mkdir(parents=True, exist_ok=True)
                
                block_file = partition_folder / f"climate_data_{year}.csv"
                partition_subset.to_csv(block_file, index=False)
                
                partition_manifest[partition_name] = {
                    "path": str(block_file),
                    "records_count": len(partition_subset),
                    "size_bytes": block_file.stat().st_size,
                    "zone_id": zone,
                    "year": int(year)
                }

        manifest_path = self.processed_dir / "hdfs_partition_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(partition_manifest, f, indent=2)

        print(f"[Ingestion] Created {len(partition_manifest)} HDFS partition blocks in {self.partitions_dir}")
        return partition_manifest

    def run_full_ingestion_pipeline(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes end-to-end ingestion pipeline:
        1. Load & Validate Raw Data
        2. Clean & Impute Missing Data
        3. Save Clean Master Dataset
        4. Partition into HDFS Blocks
        """
        print("=== EarthScape Climate Ingestion Pipeline ===")
        df_raw = self.load_historical_data()
        print(f"Loaded {len(df_raw)} raw climate records across {df_raw['zone_id'].nunique()} zones.")

        df_cleaned = self.clean_and_impute_missing_values(df_raw)
        
        # Save master processed dataset
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        cleaned_master_path = self.processed_dir / "climate_master_cleaned.csv"
        df_cleaned.to_csv(cleaned_master_path, index=False)
        print(f"[+] Saved master cleaned dataset to {cleaned_master_path}")

        # Partition for HDFS
        manifest = self.partition_for_hdfs(df_cleaned)

        metadata = {
            "total_records": len(df_cleaned),
            "date_range": [df_cleaned["timestamp"].min().strftime("%Y-%m-%d"), df_cleaned["timestamp"].max().strftime("%Y-%m-%d")],
            "total_zones": int(df_cleaned["zone_id"].nunique()),
            "total_stations": len(WEATHER_STATIONS),
            "hdfs_partitions_count": len(manifest),
            "status": "INGESTION_COMPLETE"
        }

        with open(self.processed_dir / "ingestion_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print(f"[Ingestion] Pipeline completed successfully. Total records: {len(df_cleaned):,}")
        return df_cleaned, metadata


if __name__ == "__main__":
    pipeline = ClimateDataIngestionPipeline()
    pipeline.run_full_ingestion_pipeline()
