"""
EarthScape Climate Agency - Climate Data Synthesis Module
Generates realistic, multi-source, multi-year climate datasets:
1. Historical daily weather observations across 10 global climatic zones (2015-2025).
2. Weather station network metadata and sensor configurations.
3. Greenhouse gas emissions and deforestation time series.
4. Satellite telemetry (NDVI, Sea Surface Temp, Albedo, Cloud Cover).
5. High-frequency IoT environmental sensor stream samples.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

from .static_data import CLIMATE_ZONES, WEATHER_STATIONS


def generate_historical_climate_data(start_year: int = 2015, end_year: int = 2025, seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic daily climate observation records spanning multiple years across 10 global zones.
    Includes seasonal oscillations, long-term climate warming trends, episodic extreme events, and sensor noise.
    """
    np.random.seed(seed)
    date_range = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-12-31", freq="D")
    records = []

    for zone in CLIMATE_ZONES:
        zone_id = zone["zone_id"]
        zone_name = zone["name"]
        lat = zone["lat"]
        lon = zone["lon"]
        base_temp = zone["base_temp"]
        warming_rate = zone["warming_rate"]
        base_precip = zone["base_precip"]
        climate_type = zone["climate_type"]

        # Station ID associated
        station_id = next(s["station_id"] for s in WEATHER_STATIONS if s["zone_id"] == zone_id)

        for i, dt in enumerate(date_range):
            year_offset = dt.year - start_year + (dt.dayofyear / 365.25)
            day_of_year = dt.dayofyear

            # Seasonal cycle: phase depends on Northern/Southern hemisphere
            hemisphere_factor = 1.0 if lat >= 0 else -1.0
            seasonal_temp = 12.0 * hemisphere_factor * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
            
            # Polar amplitude is larger
            if "Polar" in climate_type:
                seasonal_temp *= 1.6
            elif "Tropical" in climate_type:
                seasonal_temp *= 0.25

            # Long-term warming trend + stochastic climate variability
            trend_warming = warming_rate * year_offset
            daily_noise = np.random.normal(0, 1.8)

            # Global CO2 proxy (398 ppm in 2015 to ~425 ppm in 2025)
            co2_ppm = 398.0 + (year_offset * 2.5) + np.sin(2 * np.pi * day_of_year / 365.25) * 3.0 + np.random.normal(0, 0.4)
            ch4_ppb = 1830.0 + (year_offset * 11.2) + np.random.normal(0, 5.0)

            # Daily surface temperature
            surface_temp = round(base_temp + seasonal_temp + trend_warming + daily_noise, 2)

            # Precipitation (exponential/gamma distribution with seasonal wet/dry periods)
            precip_season = 1.0 + 0.8 * hemisphere_factor * np.sin(2 * np.pi * (day_of_year - 150) / 365.25)
            precip_scale = max(0.1, (base_precip / 30.0) * precip_season)
            precipitation_mm = round(float(np.random.exponential(precip_scale) if np.random.rand() < 0.45 else 0.0), 2)

            # Humidity (%)
            base_humidity = 82.0 if "Tropical" in climate_type or "Oceanic" in climate_type else (35.0 if "Arid" in climate_type else 65.0)
            humidity_pct = round(np.clip(base_humidity - (surface_temp - base_temp) * 0.8 + (precipitation_mm * 1.5) + np.random.normal(0, 4.0), 10.0, 100.0), 1)

            # Atmospheric Pressure (hPa)
            base_pressure = 1013.25 - (zone["lat"] * 0.1)
            pressure_hpa = round(base_pressure - (precipitation_mm * 0.3) + np.random.normal(0, 3.5), 2)

            # Wind speed (km/h)
            wind_speed_kmh = round(max(0.5, np.random.weibull(2.0) * (25.0 if "Oceanic" in climate_type or "Polar" in climate_type else 14.0)), 1)

            # Solar Irradiance (W/m^2)
            solar_irradiance = round(max(0.0, np.sin(np.pi * np.clip(day_of_year / 365.25, 0, 1)) * 320.0 + np.random.normal(0, 20.0) - (precipitation_mm * 12.0)), 1)

            # Satellite Telemetry Data (NDVI, Sea Surface Temp / Albedo, Aerosol Optical Depth)
            ndvi_val = 0.82 if "Rainforest" in climate_type else (0.12 if "Arid" in climate_type or "Polar" in climate_type else 0.58)
            ndvi = round(np.clip(ndvi_val - (trend_warming * 0.015) + (precipitation_mm * 0.002) + np.random.normal(0, 0.02), 0.0, 1.0), 3)

            ice_sheet_albedo = round(np.clip(0.85 - (trend_warming * 0.04) + np.random.normal(0, 0.015), 0.3, 0.95), 3) if "Polar" in climate_type or "Alpine" in climate_type else None
            sea_surface_temp = round(surface_temp - 1.5 + np.random.normal(0, 0.5), 2) if "Oceanic" in climate_type or "Monsoon" in climate_type else None
            aerosol_optical_depth = round(np.clip(0.15 + (year_offset * 0.008) + (0.35 if "Sahel" in zone_name or "Sahara" in zone_name else 0.0) + np.random.normal(0, 0.03), 0.02, 1.2), 3)

            # Extreme Event Classification Tag
            # Heatwave, Severe Storm/Cyclone, Extreme Drought, Polar Cold Snap, Normal
            is_heatwave = surface_temp > (base_temp + 14.0 if "Polar" not in climate_type else base_temp + 20.0)
            is_storm = precipitation_mm > 75.0 or (wind_speed_kmh > 65.0 and pressure_hpa < 990.0)
            is_drought = humidity_pct < 20.0 and precipitation_mm == 0.0 and surface_temp > (base_temp + 6.0)

            if is_heatwave:
                event_type = "HEATWAVE"
            elif is_storm:
                event_type = "SEVERE_STORM"
            elif is_drought:
                event_type = "DROUGHT"
            else:
                event_type = "NORMAL"

            records.append({
                "timestamp": dt.strftime("%Y-%m-%d"),
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "zone_id": zone_id,
                "zone_name": zone_name,
                "climate_type": climate_type,
                "station_id": station_id,
                "latitude": lat,
                "longitude": lon,
                "surface_temp_c": surface_temp,
                "precipitation_mm": precipitation_mm,
                "humidity_pct": humidity_pct,
                "pressure_hpa": pressure_hpa,
                "wind_speed_kmh": wind_speed_kmh,
                "solar_irradiance_wm2": solar_irradiance,
                "co2_ppm": round(co2_ppm, 2),
                "ch4_ppb": round(ch4_ppb, 1),
                "ndvi_vegetation_index": ndvi,
                "ice_sheet_albedo": ice_sheet_albedo,
                "sea_surface_temp_c": sea_surface_temp,
                "aerosol_optical_depth": aerosol_optical_depth,
                "extreme_event_tag": event_type
            })

    df = pd.DataFrame(records)
    return df


def generate_greenhouse_gas_data(start_year: int = 2000, end_year: int = 2025) -> pd.DataFrame:
    """
    Generates annual and monthly greenhouse gas emissions and global environmental metrics.
    """
    date_range = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-12-31", freq="MS")
    records = []

    for dt in date_range:
        year_idx = (dt.year - start_year) + (dt.month / 12.0)
        co2_ppm = 369.0 + (year_idx * 2.35) + np.sin(2 * np.pi * dt.month / 12.0) * 3.2
        ch4_ppb = 1770.0 + (year_idx * 8.5) + np.random.normal(0, 3.0)
        n2o_ppb = 315.0 + (year_idx * 0.95) + np.random.normal(0, 0.5)
        global_temp_anomaly = 0.55 + (year_idx * 0.028) + np.random.normal(0, 0.08)
        arctic_sea_ice_extent_mkm2 = max(2.5, 6.8 - (year_idx * 0.11) + np.sin(2 * np.pi * dt.month / 12.0) * 1.8)
        global_deforestation_rate_mha = max(5.0, 14.5 - (year_idx * 0.15) + np.random.normal(0, 0.6))
        fossil_fuel_emissions_gtco2 = 25.0 + (year_idx * 0.52) + np.random.normal(0, 0.4)

        records.append({
            "date": dt.strftime("%Y-%m"),
            "year": dt.year,
            "month": dt.month,
            "co2_ppm": round(co2_ppm, 2),
            "ch4_ppb": round(ch4_ppb, 1),
            "n2o_ppb": round(n2o_ppb, 2),
            "global_temp_anomaly_c": round(global_temp_anomaly, 3),
            "arctic_sea_ice_extent_mkm2": round(arctic_sea_ice_extent_mkm2, 2),
            "global_deforestation_rate_mha": round(global_deforestation_rate_mha, 2),
            "fossil_fuel_emissions_gtco2": round(fossil_fuel_emissions_gtco2, 2)
        })

    return pd.DataFrame(records)


def generate_realtime_sensor_stream_sample(n_points: int = 500) -> list:
    """
    Generates a stream sample of high-frequency IoT environmental readings.
    """
    stream_data = []
    now = pd.Timestamp.now()

    for i in range(n_points):
        station = np.random.choice(WEATHER_STATIONS)
        zone = next(z for z in CLIMATE_ZONES if z["zone_id"] == station["zone_id"])
        
        # Inject occasional anomaly
        is_spike = np.random.rand() < 0.08
        temp_spike = 15.0 if is_spike else 0.0
        co2_spike = 90.0 if is_spike else 0.0

        ts = (now - pd.Timedelta(seconds=(n_points - i) * 15)).strftime("%Y-%m-%d %H:%M:%S")

        stream_data.append({
            "reading_id": f"STRM-{100000 + i}",
            "timestamp": ts,
            "station_id": station["station_id"],
            "station_name": station["name"],
            "zone_id": station["zone_id"],
            "zone_name": zone["name"],
            "surface_temp_c": round(zone["base_temp"] + temp_spike + np.random.normal(0, 2.5), 2),
            "co2_ppm": round(420.0 + co2_spike + np.random.normal(0, 4.0), 1),
            "ch4_ppb": round(1910.0 + np.random.normal(0, 8.0), 1),
            "humidity_pct": round(np.clip(60.0 + np.random.normal(0, 15.0), 10.0, 99.0), 1),
            "pressure_hpa": round(1012.0 + np.random.normal(0, 5.0), 2),
            "wind_speed_kmh": round(max(0.5, np.random.normal(18.0, 8.0)), 1),
            "pm25_ugm3": round(max(2.0, 22.0 + (35.0 if is_spike else 0.0) + np.random.normal(0, 6.0)), 1),
            "sensor_health": "WARNING" if is_spike else "OPTIMAL"
        })

    return stream_data


def generate_all_datasets():
    """
    Executes synthesis and writes all raw datasets to data/raw/
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating climate datasets into {RAW_DATA_DIR}...")

    # 1. Historical daily climate
    df_historical = generate_historical_climate_data()
    historical_path = RAW_DATA_DIR / "climate_historical_daily.csv"
    df_historical.to_csv(historical_path, index=False)
    print(f"  [+] Saved {len(df_historical)} historical records to {historical_path.name}")

    # 2. Weather stations metadata
    stations_path = RAW_DATA_DIR / "weather_stations.json"
    with open(stations_path, "w", encoding="utf-8") as f:
        json.dump(WEATHER_STATIONS, f, indent=2)
    print(f"  [+] Saved {len(WEATHER_STATIONS)} weather station profiles to {stations_path.name}")

    # 3. Greenhouse gas emissions
    df_ghg = generate_greenhouse_gas_data()
    ghg_path = RAW_DATA_DIR / "greenhouse_gases_emissions.csv"
    df_ghg.to_csv(ghg_path, index=False)
    print(f"  [+] Saved {len(df_ghg)} greenhouse gas records to {ghg_path.name}")

    # 4. Real-time sensor stream
    stream_data = generate_realtime_sensor_stream_sample()
    stream_path = RAW_DATA_DIR / "sensor_stream_sample.json"
    with open(stream_path, "w", encoding="utf-8") as f:
        json.dump(stream_data, f, indent=2)
    print(f"  [+] Saved {len(stream_data)} real-time sensor packets to {stream_path.name}")

    # 5. Climate zones metadata
    zones_path = RAW_DATA_DIR / "climate_zones.json"
    with open(zones_path, "w", encoding="utf-8") as f:
        json.dump(CLIMATE_ZONES, f, indent=2)
    print(f"  [+] Saved {len(CLIMATE_ZONES)} climate zones to {zones_path.name}")

    print("Data synthesis complete.")


if __name__ == "__main__":
    generate_all_datasets()
