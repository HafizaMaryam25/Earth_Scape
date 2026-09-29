"""
EarthScape Climate Agency - MapReduce Job 3: Extreme Weather Pattern Detection
Identifies and categorizes extreme climate events across distributed sensor records.
"""

from typing import Iterator, Tuple, Dict, Any, List
import json
import numpy as np
import pandas as pd


class ExtremeEventMapper:
    """
    Mapper phase: Scans observation records and emits key=(zone_id, event_type), value=(event_record)
    """
    def map(self, record: Dict[str, Any]) -> Iterator[Tuple[str, Dict[str, Any]]]:
        try:
            event_type = record.get("extreme_event_tag", "NORMAL")
            zone_id = record.get("zone_id", "UNKNOWN")
            
            temp_c = float(record.get("surface_temp_c", 0.0))
            precip_mm = float(record.get("precipitation_mm", 0.0))
            wind_kmh = float(record.get("wind_speed_kmh", 0.0))
            humidity_pct = float(record.get("humidity_pct", 0.0))
            pressure_hpa = float(record.get("pressure_hpa", 1013.25))

            # Compute normalized event severity score (0.0 to 10.0)
            if event_type == "HEATWAVE":
                severity = round(min(10.0, max(1.0, (temp_c - 30.0) * 0.4 + 4.0)), 2)
            elif event_type == "SEVERE_STORM":
                severity = round(min(10.0, max(1.0, (precip_mm / 15.0) + (wind_kmh / 20.0))), 2)
            elif event_type == "DROUGHT":
                severity = round(min(10.0, max(1.0, (40.0 - humidity_pct) * 0.15 + (temp_c / 10.0))), 2)
            else:
                severity = 0.0

            key = f"{zone_id}#{event_type}"
            value = {
                "timestamp": str(record.get("timestamp", "")),
                "year": int(record.get("year", 0)),
                "zone_name": record.get("zone_name", ""),
                "climate_type": record.get("climate_type", ""),
                "temp_c": temp_c,
                "precip_mm": precip_mm,
                "wind_kmh": wind_kmh,
                "humidity_pct": humidity_pct,
                "pressure_hpa": pressure_hpa,
                "severity_score": severity
            }
            yield (key, value)
        except (ValueError, TypeError):
            pass


class ExtremeEventReducer:
    """
    Reducer phase: Aggregates total occurrences, peak severity, annual frequency, and risk index.
    """
    def reduce(self, key: str, values: List[Dict[str, Any]]) -> Dict[str, Any]:
        parts = key.split("#")
        zone_id = parts[0]
        event_type = parts[1]

        severities = [v["severity_score"] for v in values]
        years = [v["year"] for v in values]
        unique_years = len(set(years)) if years else 1

        total_occurrences = len(values)
        peak_severity = float(np.max(severities)) if severities else 0.0
        avg_severity = float(np.mean(severities)) if severities else 0.0
        annual_frequency = round(total_occurrences / max(1, unique_years), 2)

        # Composite Risk Index (0 - 100)
        risk_index = round(min(100.0, (annual_frequency * 2.5) + (avg_severity * 6.0) + (peak_severity * 2.0)), 1)

        zone_name = values[0]["zone_name"] if values else ""
        climate_type = values[0]["climate_type"] if values else ""

        # Find most severe event record
        max_idx = int(np.argmax(severities)) if severities else 0
        peak_record = values[max_idx] if values else {}

        return {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "climate_type": climate_type,
            "event_type": event_type,
            "total_occurrences": total_occurrences,
            "annual_frequency": annual_frequency,
            "peak_severity_score": round(peak_severity, 2),
            "mean_severity_score": round(avg_severity, 2),
            "climate_risk_index": risk_index,
            "peak_event_date": peak_record.get("timestamp", ""),
            "peak_temp_c": peak_record.get("temp_c", 0.0),
            "peak_wind_kmh": peak_record.get("wind_kmh", 0.0),
            "peak_precip_mm": peak_record.get("precip_mm", 0.0)
        }


def run_standalone_job(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Executes the Extreme Events MapReduce job over a DataFrame.
    """
    mapper = ExtremeEventMapper()
    reducer = ExtremeEventReducer()

    intermediate: Dict[str, List[Dict[str, Any]]] = {}
    for record in df.to_dict(orient="records"):
        for key, value in mapper.map(record):
            if key not in intermediate:
                intermediate[key] = []
            intermediate[key].append(value)

    results = []
    for key, values in sorted(intermediate.items()):
        reduced = reducer.reduce(key, values)
        results.append(reduced)

    return results
