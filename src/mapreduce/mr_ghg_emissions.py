"""
EarthScape Climate Agency - MapReduce Job 2: Greenhouse Gas Emissions & Impact Correlation
Aggregates regional GHG emissions, deforestation index, and computes correlations with surface warming.
"""

from typing import Iterator, Tuple, Dict, Any, List
import json
import numpy as np
import pandas as pd


class GHGEmissionMapper:
    """
    Mapper phase: Emits (Key=year, Value=(co2_ppm, ch4_ppb, temp_c, ndvi, aerosol, zone_id))
    """
    def map(self, record: Dict[str, Any]) -> Iterator[Tuple[str, Dict[str, Any]]]:
        try:
            year = str(record.get("year", "0"))
            co2 = float(record.get("co2_ppm", 0.0))
            ch4 = float(record.get("ch4_ppb", 0.0))
            temp = float(record.get("surface_temp_c", 0.0))
            ndvi = float(record.get("ndvi_vegetation_index", 0.0)) if record.get("ndvi_vegetation_index") is not None else 0.5
            aerosol = float(record.get("aerosol_optical_depth", 0.0)) if record.get("aerosol_optical_depth") is not None else 0.1
            
            value = {
                "co2_ppm": co2,
                "ch4_ppb": ch4,
                "surface_temp_c": temp,
                "ndvi": ndvi,
                "aerosol": aerosol,
                "zone_id": record.get("zone_id", "UNKNOWN")
            }
            yield (year, value)
        except (ValueError, TypeError):
            pass


class GHGEmissionReducer:
    """
    Reducer phase: Aggregates annual statistics, computes global CO2 growth rates,
    vegetation index degradation, and correlation between CO2 and surface temperatures.
    """
    def reduce(self, key: str, values: List[Dict[str, Any]]) -> Dict[str, Any]:
        year = int(key)
        co2_vals = [v["co2_ppm"] for v in values]
        ch4_vals = [v["ch4_ppb"] for v in values]
        temp_vals = [v["surface_temp_c"] for v in values]
        ndvi_vals = [v["ndvi"] for v in values]
        aerosol_vals = [v["aerosol"] for v in values]

        avg_co2 = float(np.mean(co2_vals))
        avg_ch4 = float(np.mean(ch4_vals))
        avg_temp = float(np.mean(temp_vals))
        avg_ndvi = float(np.mean(ndvi_vals))
        avg_aerosol = float(np.mean(aerosol_vals))

        # Correlation between CO2 and surface temp for this year across records
        if len(co2_vals) > 1 and np.std(co2_vals) > 0 and np.std(temp_vals) > 0:
            corr_co2_temp = float(np.corrcoef(co2_vals, temp_vals)[0, 1])
        else:
            corr_co2_temp = 0.0

        return {
            "year": year,
            "sample_count": len(values),
            "mean_co2_ppm": round(avg_co2, 2),
            "mean_ch4_ppb": round(avg_ch4, 1),
            "mean_surface_temp_c": round(avg_temp, 2),
            "mean_ndvi_index": round(avg_ndvi, 3),
            "mean_aerosol_optical_depth": round(avg_aerosol, 3),
            "co2_temp_correlation": round(corr_co2_temp, 3),
            "co2_min_max": [round(float(np.min(co2_vals)), 1), round(float(np.max(co2_vals)), 1)]
        }


def run_standalone_job(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Executes the GHG Emissions MapReduce job over a DataFrame.
    """
    mapper = GHGEmissionMapper()
    reducer = GHGEmissionReducer()

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
