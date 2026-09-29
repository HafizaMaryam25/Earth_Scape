"""
EarthScape Climate Agency - MapReduce Job 1: Temperature Anomalies & Baseline Deviation
Calculates long-term baseline monthly climatological means and rolling temperature anomalies per zone.
"""

from typing import Iterator, Tuple, Dict, Any, List
import json
import numpy as np
import pandas as pd


class TemperatureAnomalyMapper:
    """
    Mapper phase: Emits (Key=(zone_id, month), Value=(surface_temp_c, year, timestamp))
    """
    def map(self, record: Dict[str, Any]) -> Iterator[Tuple[str, Dict[str, Any]]]:
        try:
            zone_id = record.get("zone_id", "UNKNOWN")
            month = int(record.get("month", 0))
            temp_c = float(record.get("surface_temp_c", 0.0))
            year = int(record.get("year", 0))
            timestamp = str(record.get("timestamp", ""))
            
            key = f"{zone_id}#{month:02d}"
            value = {
                "temp_c": temp_c,
                "year": year,
                "timestamp": timestamp,
                "zone_name": record.get("zone_name", ""),
                "climate_type": record.get("climate_type", "")
            }
            yield (key, value)
        except (ValueError, TypeError):
            pass


class TemperatureAnomalyReducer:
    """
    Reducer phase: Calculates baseline climatology for (zone, month) and computes individual anomalies.
    Also produces monthly aggregated anomalies over time.
    """
    def reduce(self, key: str, values: List[Dict[str, Any]]) -> Dict[str, Any]:
        parts = key.split("#")
        zone_id = parts[0]
        month = int(parts[1])

        temps = [v["temp_c"] for v in values]
        baseline_mean = float(np.mean(temps))
        baseline_std = float(np.std(temps))

        # Calculate anomaly for each record against monthly climatological baseline
        yearly_anomalies: Dict[int, List[float]] = {}
        for v in values:
            y = v["year"]
            anomaly = v["temp_c"] - baseline_mean
            if y not in yearly_anomalies:
                yearly_anomalies[y] = []
            yearly_anomalies[y].append(anomaly)

        yearly_summary = {
            year: round(float(np.mean(anoms)), 3)
            for year, anoms in sorted(yearly_anomalies.items())
        }

        zone_name = values[0]["zone_name"] if values else ""
        climate_type = values[0]["climate_type"] if values else ""

        return {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "climate_type": climate_type,
            "month": month,
            "record_count": len(values),
            "climatological_mean_c": round(baseline_mean, 2),
            "climatological_std_c": round(baseline_std, 2),
            "min_temp_c": round(float(np.min(temps)), 2),
            "max_temp_c": round(float(np.max(temps)), 2),
            "yearly_mean_anomalies_c": yearly_summary
        }


def run_standalone_job(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Executes the Temperature Anomaly MapReduce job over a DataFrame.
    """
    mapper = TemperatureAnomalyMapper()
    reducer = TemperatureAnomalyReducer()

    # Map Phase
    intermediate: Dict[str, List[Dict[str, Any]]] = {}
    for record in df.to_dict(orient="records"):
        for key, value in mapper.map(record):
            if key not in intermediate:
                intermediate[key] = []
            intermediate[key].append(value)

    # Reduce Phase
    results = []
    for key, values in sorted(intermediate.items()):
        reduced = reducer.reduce(key, values)
        results.append(reduced)

    return results
