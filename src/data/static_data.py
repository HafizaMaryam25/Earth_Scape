"""EarthScape Climate Agency - Centralized Static / Seed Data.

Keep application seed/configuration data here instead of embedding it inside
API handlers or data-generation logic. Runtime datasets remain in data/raw/
and data/processed/.
"""

# Global Climatic Zones
CLIMATE_ZONES = [
    {"zone_id": "Z01", "name": "Arctic Polar Region", "lat": 78.22, "lon": 15.65, "base_temp": -12.5, "warming_rate": 0.085, "base_precip": 35.0, "climate_type": "Polar"},
    {"zone_id": "Z02", "name": "Sahara Arid Basin", "lat": 23.41, "lon": 25.66, "base_temp": 31.0, "warming_rate": 0.048, "base_precip": 4.0, "climate_type": "Hyper-Arid"},
    {"zone_id": "Z03", "name": "Amazon Tropical Rainforest", "lat": -3.46, "lon": -62.21, "base_temp": 27.2, "warming_rate": 0.038, "base_precip": 240.0, "climate_type": "Tropical Rainforest"},
    {"zone_id": "Z04", "name": "North Atlantic Marine", "lat": 45.10, "lon": -30.20, "base_temp": 11.8, "warming_rate": 0.042, "base_precip": 95.0, "climate_type": "Oceanic"},
    {"zone_id": "Z05", "name": "Indo-Pacific Monsoon Basin", "lat": 12.87, "lon": 100.52, "base_temp": 28.5, "warming_rate": 0.045, "base_precip": 180.0, "climate_type": "Tropical Monsoon"},
    {"zone_id": "Z06", "name": "Himalayan Alpine Region", "lat": 28.00, "lon": 86.85, "base_temp": -2.4, "warming_rate": 0.065, "base_precip": 70.0, "climate_type": "Alpine Tundra"},
    {"zone_id": "Z07", "name": "Western European Temperate", "lat": 48.85, "lon": 2.35, "base_temp": 12.2, "warming_rate": 0.040, "base_precip": 65.0, "climate_type": "Temperate Maritime"},
    {"zone_id": "Z08", "name": "North American Continental", "lat": 41.87, "lon": -87.62, "base_temp": 10.5, "warming_rate": 0.041, "base_precip": 82.0, "climate_type": "Humid Continental"},
    {"zone_id": "Z09", "name": "Sub-Saharan Sahel Region", "lat": 14.49, "lon": 14.45, "base_temp": 29.8, "warming_rate": 0.052, "base_precip": 45.0, "climate_type": "Semi-Arid"},
    {"zone_id": "Z10", "name": "Australian Outback", "lat": -25.27, "lon": 133.77, "base_temp": 24.5, "warming_rate": 0.046, "base_precip": 25.0, "climate_type": "Arid Continental"},
]

# Weather Station Metadata
WEATHER_STATIONS = [
    {"station_id": "WS-ARC-01", "zone_id": "Z01", "name": "Svalbard Arctic Observatory", "lat": 78.22, "lon": 15.65, "elevation_m": 120, "sensor_count": 24, "status": "ACTIVE", "firmware_version": "v4.2.1"},
    {"station_id": "WS-SAH-02", "zone_id": "Z02", "name": "Kufra Desert Climate Hub", "lat": 23.41, "lon": 25.66, "elevation_m": 416, "sensor_count": 18, "status": "ACTIVE", "firmware_version": "v3.9.0"},
    {"station_id": "WS-AMZ-03", "zone_id": "Z03", "name": "Manaus Canopy Tower", "lat": -3.46, "lon": -62.21, "elevation_m": 85, "sensor_count": 32, "status": "ACTIVE", "firmware_version": "v4.5.0"},
    {"station_id": "WS-NAT-04", "zone_id": "Z04", "name": "Azores Oceanographic Buoy", "lat": 45.10, "lon": -30.20, "elevation_m": 0, "sensor_count": 16, "status": "ACTIVE", "firmware_version": "v4.1.2"},
    {"station_id": "WS-IND-05", "zone_id": "Z05", "name": "Gulf of Thailand Coastal Station", "lat": 12.87, "lon": 100.52, "elevation_m": 12, "sensor_count": 28, "status": "ACTIVE", "firmware_version": "v4.4.1"},
    {"station_id": "WS-HIM-06", "zone_id": "Z06", "name": "Khumbu Glacier Met Station", "lat": 28.00, "lon": 86.85, "elevation_m": 5050, "sensor_count": 22, "status": "ACTIVE", "firmware_version": "v3.8.4"},
    {"station_id": "WS-EUR-07", "zone_id": "Z07", "name": "Paris Basin Agro-Climatic Center", "lat": 48.85, "lon": 2.35, "elevation_m": 55, "sensor_count": 30, "status": "ACTIVE", "firmware_version": "v4.6.0"},
    {"station_id": "WS-NAC-08", "zone_id": "Z08", "name": "Great Lakes Environmental Base", "lat": 41.87, "lon": -87.62, "elevation_m": 182, "sensor_count": 26, "status": "ACTIVE", "firmware_version": "v4.3.3"},
    {"station_id": "WS-SAH-09", "zone_id": "Z09", "name": "Niamey Sahelian Research Station", "lat": 14.49, "lon": 14.45, "elevation_m": 227, "sensor_count": 20, "status": "ACTIVE", "firmware_version": "v4.0.1"},
    {"station_id": "WS-AUS-10", "zone_id": "Z10", "name": "Alice Springs Arid Observatory", "lat": -25.27, "lon": 133.77, "elevation_m": 546, "sensor_count": 24, "status": "ACTIVE", "firmware_version": "v4.2.0"},
]

# Default Alert Thresholds
DEFAULT_ALERT_CONFIG = {
    "temp_heatwave_c": 38.0,
    "temp_arctic_anomaly_c": 6.0,
    "co2_critical_ppm": 440.0,
    "wind_storm_kmh": 65.0,
    "pm25_unhealthy_ugm3": 55.0,
    "pressure_cyclone_drop_hpa": 988.0,
    "email_notifications": True,
    "sms_broadcast": False,
}

# Initial support tickets
DEFAULT_TICKETS = [
    {
        "ticket_id": "TCK-801",
        "title": "Temperature sensor calibration drift at Manaus Canopy Tower",
        "category": "Sensor Calibration",
        "priority": "HIGH",
        "status": "IN_PROGRESS",
        "author": "Dr. Elena Rostova (Lead Meteorologist)",
        "station_id": "WS-AMZ-03",
        "created_at": "2026-08-30 09:15:00",
        "description": "Observed a +1.8°C nocturnal baseline offset relative to eddy covariance tower. Needs field recalibration.",
    },
    {
        "ticket_id": "TCK-802",
        "title": "HDFS block replication warning on DataNode-03",
        "category": "Infrastructure",
        "priority": "MEDIUM",
        "status": "RESOLVED",
        "author": "Marcus Vance (Systems Architect)",
        "station_id": "ALL",
        "created_at": "2026-08-29 14:30:00",
        "description": "Transient network partition triggered automated under-replication alert. Self-healed across rack-2.",
    },
    {
        "ticket_id": "TCK-803",
        "title": "Request for NetCDF format export in Polar Climate analysis",
        "category": "Feature Request",
        "priority": "LOW",
        "status": "OPEN",
        "author": "Prof. T. Lindholm (Arctic Research Council)",
        "station_id": "WS-ARC-01",
        "created_at": "2026-08-31 11:20:00",
        "description": "Analyst team requires gridded NetCDF4 exports for multi-decadal sea-ice albedo comparison studies.",
    },
]

# Demo accounts are seed data only; production users must be created through auth.
DEMO_ACCOUNTS = [
    {"name": "System Administrator", "email": "admin@earthscape.org", "password": "admin123", "role": "admin"},
    {"name": "Sarah Chen", "email": "sarah.chen@earthscape.org", "password": "analyst2026", "role": "analyst"},
    {"name": "James Okafor", "email": "james.okafor@earthscape.org", "password": "analyst2026", "role": "analyst"},
    {"name": "Priya Sharma", "email": "priya.sharma@earthscape.org", "password": "analyst2026", "role": "analyst"},
]
