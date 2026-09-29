"""
EarthScape Climate Agency - Central Application Server & REST API
Provides high-performance endpoints for:
- Climate Vitals & Observations
- Weather Station Directory & Live Telemetry
- Hadoop HDFS & MapReduce Job Execution
- Machine Learning Inference (Forecasting, Anomaly Detection, Impact Analysis)
- Automated Early Warning Alerts & Threshold Management
- Support Ticketing & User Feedback System
- Cluster & System Performance Monitoring
- Web UI Static Assets
"""

import sys
import os
import http.server
import socketserver
import json
import urllib.parse
from pathlib import Path
import time
import random
import hashlib
import joblib
import numpy as np
import pandas as pd

# Load environment variables from .env before anything else
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
for p in [str(PROJECT_ROOT), str(SRC_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from src.data.ingestion import ClimateDataIngestionPipeline
    from src.data.static_data import CLIMATE_ZONES, DEFAULT_ALERT_CONFIG, DEFAULT_TICKETS
    from src.hadoop.hdfs_manager import HDFSClusterManager
    from src.mapreduce.mr_job_runner import MapReduceJobRunner
    from src.ml.forecast_model import engineer_climate_features
    from src.ml.anomaly_model import predict_anomalies
    from src.ml.impact_model import IMPACT_FEATURES
except ImportError:
    from data.ingestion import ClimateDataIngestionPipeline
    from data.static_data import CLIMATE_ZONES, DEFAULT_ALERT_CONFIG, DEFAULT_TICKETS
    from hadoop.hdfs_manager import HDFSClusterManager
    from mapreduce.mr_job_runner import MapReduceJobRunner
    from ml.forecast_model import engineer_climate_features
    from ml.anomaly_model import predict_anomalies
    from ml.impact_model import IMPACT_FEATURES

WEB_DIR = PROJECT_ROOT / "web"
MODEL_DIR = PROJECT_ROOT / "models"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TICKETS_FILE = PROCESSED_DIR / "support_tickets.json"
ALERTS_CONFIG_FILE = PROCESSED_DIR / "alerts_config.json"

PORT = int(os.getenv("PORT", "8000"))

# ─────────────────────────────────────────────────────────
# Authentication & Role-Based Access Control (RBAC)
# Users are stored in SQL Server LocalDB (EarthScapeDb). See db.py for schema and operations.
# ─────────────────────────────────────────────────────────
import db as user_db

ROLE_HIERARCHY = {"admin": 2, "analyst": 1}

# In-memory session store: token -> {"email", "role", "display_name", "created_at"}
active_sessions: dict = {}

def _generate_token() -> str:
    raw = f"{time.time()}-{random.randint(100000, 999999)}-{random.random()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]

def authenticate_user(email: str, password: str) -> dict | None:
    """Look up user in SQL, verify bcrypt password, create session token."""
    user = user_db.find_user_by_email(email)
    if user and user_db.verify_password(password, user["PasswordHash"]):
        token = _generate_token()
        active_sessions[token] = {
            "email": user["Email"],
            "role": user["Role"],
            "display_name": user["Name"],
            "created_at": time.time()
        }
        return {"token": token, "role": user["Role"], "display_name": user["Name"], "email": user["Email"]}
    return None

def get_session_from_token(token: str) -> dict | None:
    return active_sessions.get(token)

def check_role_permission(request_handler, required_role: str) -> bool:
    """Returns True if the request has sufficient role permissions."""
    auth_header = request_handler.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        session = get_session_from_token(token)
        if session:
            return ROLE_HIERARCHY.get(session["role"], 0) >= ROLE_HIERARCHY.get(required_role, 0)
    return False


class EarthScapeAPIHandler(http.server.SimpleHTTPRequestHandler):
    """
    REST API and static content request dispatcher.
    """
    ingestion = ClimateDataIngestionPipeline()
    hdfs = HDFSClusterManager()
    mr_runner = MapReduceJobRunner()

    model_cache = {}

    @classmethod
    def get_model(cls, model_name: str):
        if model_name not in cls.model_cache:
            model_path = MODEL_DIR / f"{model_name}.joblib"
            if model_path.exists():
                cls.model_cache[model_name] = joblib.load(model_path)
            else:
                return None
        return cls.model_cache[model_name]

    def _send_json(self, data, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/vitals":
            self.handle_get_vitals()
        elif path == "/api/stations":
            self.handle_get_stations()
        elif path == "/api/zones":
            self.handle_get_zones()
        elif path == "/api/historical":
            self.handle_get_historical(params)
        elif path == "/api/ghg":
            self.handle_get_ghg()
        elif path == "/api/mapreduce/status":
            self.handle_get_mapreduce_status()
        elif path == "/api/stream/telemetry":
            self.handle_get_stream_telemetry()
        elif path == "/api/alerts":
            self.handle_get_alerts()
        elif path == "/api/alerts/config":
            self.handle_get_alerts_config()
        elif path == "/api/tickets":
            self.handle_get_tickets()
        elif path == "/api/system/health":
            self.handle_get_system_health()
        elif path == "/api/models/summary":
            self.handle_get_models_summary()
        elif path == "/api/auth/me":
            self.handle_get_auth_me()
        elif path.startswith("/api/"):
            self._send_json({"error": "Endpoint not found"}, status=404)
        else:
            # Serve Static Web UI files
            if path == "/" or path == "":
                self.path = "/web/index.html"
            elif not path.startswith("/web/"):
                self.path = f"/web{path}"
            return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}

        try:
            if path == "/api/auth/login":
                self.handle_post_auth_login(payload)
            elif path == "/api/auth/register":
                self.handle_post_auth_register(payload)
            elif path == "/api/auth/logout":
                self.handle_post_auth_logout()
            elif path == "/api/mapreduce/run":
                if not check_role_permission(self, "analyst"):
                    self._send_json({"error": "Permission denied: Analyst role or higher required"}, status=403)
                    return
                self.handle_post_mapreduce_run(payload)
            elif path == "/api/predict/forecast":
                if not check_role_permission(self, "analyst"):
                    self._send_json({"error": "Permission denied: Analyst role or higher required"}, status=403)
                    return
                self.handle_post_predict_forecast(payload)
            elif path == "/api/predict/anomaly":
                if not check_role_permission(self, "analyst"):
                    self._send_json({"error": "Permission denied: Analyst role or higher required"}, status=403)
                    return
                self.handle_post_predict_anomaly(payload)
            elif path == "/api/predict/impact":
                if not check_role_permission(self, "analyst"):
                    self._send_json({"error": "Permission denied: Analyst role or higher required"}, status=403)
                    return
                self.handle_post_predict_impact(payload)
            elif path == "/api/alerts/config":
                if not check_role_permission(self, "analyst"):
                    self._send_json({"error": "Permission denied: Analyst role or higher required"}, status=403)
                    return
                self.handle_post_alerts_config(payload)
            elif path == "/api/tickets":
                self.handle_post_tickets_create(payload)
            elif path == "/api/tickets/update":
                if not check_role_permission(self, "admin"):
                    self._send_json({"error": "Permission denied: Admin role required"}, status=403)
                    return
                self.handle_post_tickets_update(payload)
            else:
                self._send_json({"error": "Endpoint not found"}, status=404)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            try:
                self._send_json({"error": str(exc)}, status=500)
            except Exception:
                pass

    # -----------------------------------------------------------------
    # Handler Implementations
    # -----------------------------------------------------------------
    def handle_post_auth_login(self, payload):
        email = payload.get("email", "")
        password = payload.get("password", "")
        try:
            result = authenticate_user(email, password)
        except Exception:
            self._send_json({"error": "Authentication service error"}, status=500)
            return
        if result:
            self._send_json({"status": "SUCCESS", **result})
        else:
            self._send_json({"error": "Invalid credentials"}, status=401)

    def handle_post_auth_register(self, payload):
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")
        display_name = payload.get("display_name", "").strip()

        if not email or not password or not display_name:
            self._send_json({"error": "All fields are required"}, status=400)
            return
        if len(password) < 4:
            self._send_json({"error": "Password must be at least 4 characters"}, status=400)
            return
        # Block role injection: never trust client-supplied role
        if payload.get("role"):
            self._send_json({"error": "Role selection is not allowed during registration"}, status=403)
            return

        try:
            # Insert into SQL — role is always 'analyst'
            user_db.create_user(display_name, email, password, role="analyst")
        except ValueError as e:
            self._send_json({"error": str(e)}, status=409)
            return

        # Auto-login after successful registration
        result = authenticate_user(email, password)
        if result:
            self._send_json({"status": "SUCCESS", **result})
        else:
            self._send_json({"error": "Registration failed unexpectedly"}, status=500)

    def handle_post_auth_logout(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            active_sessions.pop(token, None)
        self._send_json({"status": "LOGGED_OUT"})

    def handle_get_auth_me(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            session = get_session_from_token(token)
            if session:
                self._send_json({"authenticated": True, **session})
                return
        self._send_json({"authenticated": False}, status=401)

    def handle_get_zones(self):
        """Returns aggregated zone-level data for the zones table."""
        from src.data.generator import CLIMATE_ZONES as ZONES_DATA
        df_hist = self.ingestion.load_historical_data()
        zones_output = []
        for z in ZONES_DATA:
            zone_df = df_hist[df_hist["zone_id"] == z["zone_id"]]
            block_count = len(list((PROCESSED_DIR / "hdfs_partitions" / f"zone={z['zone_id']}").glob("*.csv"))) if (PROCESSED_DIR / "hdfs_partitions" / f"zone={z['zone_id']}").exists() else 0
            zones_output.append({
                "zone_id": z["zone_id"],
                "name": z["name"],
                "lat": z["lat"],
                "lon": z["lon"],
                "climate_type": z["climate_type"],
                "base_temp": z["base_temp"],
                "warming_rate": z["warming_rate"],
                "partition_blocks": block_count,
                "record_count": len(zone_df),
                "status": "ONLINE"
            })
        self._send_json(zones_output)

    def handle_get_vitals(self):
        df_ghg = self.ingestion.load_greenhouse_gas_data()
        latest_ghg = df_ghg.iloc[-1].to_dict()
        df_hist = self.ingestion.load_historical_data()

        # Quick alert count: check how many zones exceed heatwave threshold
        if ALERTS_CONFIG_FILE.exists():
            with open(ALERTS_CONFIG_FILE, "r", encoding="utf-8") as f:
                alert_cfg = json.load(f)
        else:
            alert_cfg = DEFAULT_ALERT_CONFIG
        heatwave_t = float(alert_cfg.get("temp_heatwave_c", 38.0))
        recent = df_hist.sort_values("timestamp").tail(len(df_hist) // 5)
        alert_count = int(recent.groupby("zone_id")["surface_temp_c"].max().gt(heatwave_t).sum())
        alert_count += 1 if float(latest_ghg.get("co2_ppm", 0)) > float(alert_cfg.get("co2_critical_ppm", 440.0)) else 0
        alert_count = max(alert_count, 1)  # At least 1 for visibility

        vitals = {
            "global_temp_anomaly_c": round(float(latest_ghg.get("global_temp_anomaly_c", 1.28)), 3),
            "atmospheric_co2_ppm": round(float(latest_ghg.get("co2_ppm", 424.5)), 1),
            "atmospheric_ch4_ppb": round(float(latest_ghg.get("ch4_ppb", 1928.0)), 1),
            "arctic_sea_ice_mkm2": round(float(latest_ghg.get("arctic_sea_ice_extent_mkm2", 4.15)), 2),
            "deforestation_rate_mha": round(float(latest_ghg.get("global_deforestation_rate_mha", 10.4)), 2),
            "active_weather_stations": 10,
            "total_ingested_records": len(df_hist),
            "active_alerts_count": alert_count,
            "hdfs_cluster_health": "OPTIMAL (100% Replicated)",
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        self._send_json(vitals)

    def handle_get_stations(self):
        stations = self.ingestion.load_weather_stations()
        df_hist = self.ingestion.load_historical_data()

        enriched_stations = []
        for st in stations:
            st_records = df_hist[df_hist["station_id"] == st["station_id"]]
            latest = st_records.iloc[-1] if not st_records.empty else None
            
            st_data = dict(st)
            if latest is not None:
                st_data["current_temp_c"] = float(latest["surface_temp_c"])
                st_data["current_humidity_pct"] = float(latest["humidity_pct"])
                st_data["current_pressure_hpa"] = float(latest["pressure_hpa"])
                st_data["current_wind_kmh"] = float(latest["wind_speed_kmh"])
                st_data["current_co2_ppm"] = float(latest["co2_ppm"])
                st_data["latest_event"] = str(latest["extreme_event_tag"])
                st_data["anomaly_risk"] = "HIGH" if latest["extreme_event_tag"] != "NORMAL" else "LOW"
            enriched_stations.append(st_data)

        self._send_json(enriched_stations)

    def handle_get_historical(self, params):
        zone_id = params.get("zone_id", ["ALL"])[0]
        df = self.ingestion.load_historical_data()
        if zone_id != "ALL":
            df = df[df["zone_id"] == zone_id]

        df["year_month"] = df["timestamp"].dt.strftime("%Y-%m")
        grouped = df.groupby("year_month").agg({
            "surface_temp_c": "mean",
            "co2_ppm": "mean",
            "precipitation_mm": "sum",
            "humidity_pct": "mean",
            "wind_speed_kmh": "mean"
        }).reset_index()

        output = {
            "labels": grouped["year_month"].tolist(),
            "temperatures": [round(float(x), 2) for x in grouped["surface_temp_c"].tolist()],
            "co2": [round(float(x), 1) for x in grouped["co2_ppm"].tolist()],
            "precipitation": [round(float(x), 1) for x in grouped["precipitation_mm"].tolist()],
            "humidity": [round(float(x), 1) for x in grouped["humidity_pct"].tolist()]
        }
        self._send_json(output)

    def handle_get_ghg(self):
        df_ghg = self.ingestion.load_greenhouse_gas_data()
        self._send_json(df_ghg.to_dict(orient="records"))

    def handle_get_mapreduce_status(self):
        status = self.hdfs.get_cluster_status()
        self._send_json(status)

    def handle_get_stream_telemetry(self):
        stations = self.ingestion.load_weather_stations()
        st = random.choice(stations)
        
        is_spike = random.random() < 0.12
        temp_spike = random.uniform(8.0, 18.0) if is_spike else 0.0
        co2_spike = random.uniform(40.0, 90.0) if is_spike else 0.0

        base_temp = 24.0 if "AMZ" in st["station_id"] or "IND" in st["station_id"] else (
            -8.0 if "ARC" in st["station_id"] else (32.0 if "SAH" in st["station_id"] else 15.0)
        )

        packet = {
            "reading_id": f"STRM-{int(time.time()*1000) % 1000000}",
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "station_id": st["station_id"],
            "station_name": st["name"],
            "zone_id": st["zone_id"],
            "surface_temp_c": round(base_temp + temp_spike + random.gauss(0, 1.5), 2),
            "co2_ppm": round(422.0 + co2_spike + random.gauss(0, 2.0), 1),
            "ch4_ppb": round(1915.0 + random.gauss(0, 5.0), 1),
            "humidity_pct": round(min(100.0, max(12.0, 60.0 + random.gauss(0, 12.0))), 1),
            "pressure_hpa": round(1012.5 + random.gauss(0, 3.5), 2),
            "wind_speed_kmh": round(max(1.0, random.gauss(18.0, 6.0)), 1),
            "pm25_ugm3": round(max(2.0, 18.0 + (45.0 if is_spike else 0.0) + random.gauss(0, 4.0)), 1),
            "is_anomaly": is_spike,
            "anomaly_reason": "CRITICAL THERMAL/CO2 SPIKE" if is_spike else "NORMAL_BASELINE"
        }
        self._send_json(packet)

    def handle_get_alerts(self):
        """Generate dynamic alerts from actual data and configured thresholds."""
        # Load current alert config thresholds
        if ALERTS_CONFIG_FILE.exists():
            with open(ALERTS_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = DEFAULT_ALERT_CONFIG

        heatwave_thresh = float(config.get("temp_heatwave_c", 38.0))
        arctic_anom_thresh = float(config.get("temp_arctic_anomaly_c", 6.0))
        co2_critical = float(config.get("co2_critical_ppm", 440.0))
        wind_storm_thresh = float(config.get("wind_storm_kmh", 65.0))
        pm25_thresh = float(config.get("pm25_unhealthy_ugm3", 55.0))
        pressure_thresh = float(config.get("pressure_cyclone_drop_hpa", 988.0))

        # Load recent data for alert generation
        df_hist = self.ingestion.load_historical_data()
        stations = self.ingestion.load_weather_stations()
        df_ghg = self.ingestion.load_greenhouse_gas_data()

        alerts = []
        alert_counter = 89

        # Check each zone for threshold breaches using recent data (last 90 days)
        recent_df = df_hist.sort_values("timestamp").tail(len(df_hist) // 5)

        for zone_id in recent_df["zone_id"].unique():
            zone_data = recent_df[recent_df["zone_id"] == zone_id]
            zone_name = zone_data.iloc[0]["zone_name"] if not zone_data.empty else zone_id
            max_temp = float(zone_data["surface_temp_c"].max())
            max_wind = float(zone_data["wind_speed_kmh"].max())
            min_pressure = float(zone_data["pressure_hpa"].min())

            # Heatwave check
            if max_temp > heatwave_thresh:
                alert_counter += 1
                severity = "CRITICAL" if max_temp > heatwave_thresh + 6 else "HIGH"
                alerts.append({
                    "alert_id": f"ALT-2026-{alert_counter:03d}",
                    "severity": severity,
                    "title": "Severe Heatwave & Wildfire Danger Warning",
                    "zone_id": zone_id,
                    "zone_name": zone_name,
                    "metric_triggered": f"surface_temp_c > {heatwave_thresh}°C",
                    "current_value": f"{max_temp:.1f}°C",
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "action_required": "Activate heat emergency protocols and ground solar field cooling.",
                    "status": "ACTIVE"
                })

            # Storm check
            if max_wind > wind_storm_thresh:
                alert_counter += 1
                alerts.append({
                    "alert_id": f"ALT-2026-{alert_counter:03d}",
                    "severity": "HIGH",
                    "title": "Severe Storm Wind Speed Advisory",
                    "zone_id": zone_id,
                    "zone_name": zone_name,
                    "metric_triggered": f"wind_speed_kmh > {wind_storm_thresh}",
                    "current_value": f"{max_wind:.1f} km/h",
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "action_required": "Issue storm warnings and activate shelter protocols.",
                    "status": "ACTIVE"
                })

            # Cyclone/low-pressure check
            if min_pressure < pressure_thresh:
                alert_counter += 1
                alerts.append({
                    "alert_id": f"ALT-2026-{alert_counter:03d}",
                    "severity": "HIGH",
                    "title": "Low Pressure Cyclone Alert",
                    "zone_id": zone_id,
                    "zone_name": zone_name,
                    "metric_triggered": f"pressure_hpa < {pressure_thresh}",
                    "current_value": f"{min_pressure:.1f} hPa",
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "action_required": "Activate cyclone monitoring and regional flood telemetry.",
                    "status": "MONITORING"
                })

        # Arctic anomaly check (Z01 specific)
        arctic_data = recent_df[recent_df["zone_id"] == "Z01"]
        if not arctic_data.empty:
            arctic_mean = float(arctic_data["surface_temp_c"].mean())
            # Compare to global baseline
            global_mean = float(df_hist["surface_temp_c"].mean())
            arctic_anomaly = arctic_mean - (df_hist[df_hist["zone_id"] == "Z01"]["surface_temp_c"].mean() - arctic_anom_thresh)
            if arctic_anomaly > arctic_anom_thresh:
                alert_counter += 1
                alerts.append({
                    "alert_id": f"ALT-2026-{alert_counter:03d}",
                    "severity": "HIGH",
                    "title": "Polar Ice Albedo Acceleration Alert",
                    "zone_id": "Z01",
                    "zone_name": "Arctic Polar Region",
                    "metric_triggered": f"temp_anomaly > +{arctic_anom_thresh}°C",
                    "current_value": f"+{arctic_anomaly:.1f}°C baseline anomaly",
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "action_required": "Deploy targeted SAR satellite high-resolution glacier scanning.",
                    "status": "ACTIVE"
                })

        # CO2 critical breach check
        latest_ghg = df_ghg.iloc[-1]
        latest_co2 = float(latest_ghg.get("co2_ppm", 0))
        if latest_co2 > co2_critical:
            alert_counter += 1
            alerts.append({
                "alert_id": f"ALT-2026-{alert_counter:03d}",
                "severity": "CRITICAL",
                "title": "Atmospheric CO2 Critical Threshold Breach",
                "zone_id": "GLOBAL",
                "zone_name": "Global Atmosphere",
                "metric_triggered": f"co2_ppm > {co2_critical}",
                "current_value": f"{latest_co2:.1f} ppm",
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "action_required": "Escalate to global environmental agencies for emission review.",
                "status": "ACTIVE"
            })

        # Precipitation flood advisory (check zones with high recent precipitation)
        for zone_id in recent_df["zone_id"].unique():
            zone_data = recent_df[recent_df["zone_id"] == zone_id]
            max_precip = float(zone_data["precipitation_mm"].max())
            if max_precip > 75.0:
                zone_name = zone_data.iloc[0]["zone_name"]
                alert_counter += 1
                alerts.append({
                    "alert_id": f"ALT-2026-{alert_counter:03d}",
                    "severity": "MODERATE",
                    "title": "Precipitation & Flash Flood Advisory",
                    "zone_id": zone_id,
                    "zone_name": zone_name,
                    "metric_triggered": "precipitation_24h > 75mm",
                    "current_value": f"{max_precip:.1f} mm",
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "action_required": "Alert regional flood telemetry sensors and hydrological dams.",
                    "status": "MONITORING"
                })

        # Sort alerts: CRITICAL first, then HIGH, then MODERATE
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}
        alerts.sort(key=lambda a: severity_order.get(a["severity"], 99))

        # Limit to top 10 most important alerts
        alerts = alerts[:10]

        self._send_json(alerts)

    def handle_get_alerts_config(self):
        if ALERTS_CONFIG_FILE.exists():
            with open(ALERTS_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = DEFAULT_ALERT_CONFIG
        self._send_json(config)

    def handle_post_alerts_config(self, payload):
        with open(ALERTS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        self._send_json({"status": "SUCCESS", "message": "Alert thresholds updated successfully.", "config": payload})

    def handle_get_tickets(self):
        if TICKETS_FILE.exists():
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                tickets = json.load(f)
        else:
            tickets = DEFAULT_TICKETS
            with open(TICKETS_FILE, "w", encoding="utf-8") as f:
                json.dump(tickets, f, indent=2)
        self._send_json(tickets)

    def handle_post_tickets_create(self, payload):
        tickets = []
        if TICKETS_FILE.exists():
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                tickets = json.load(f)
        else:
            tickets = list(DEFAULT_TICKETS)

        new_ticket = {
            "ticket_id": f"TCK-{random.randint(804, 999)}",
            "title": payload.get("title", "Untitled Feedback"),
            "category": payload.get("category", "General"),
            "priority": payload.get("priority", "MEDIUM"),
            "status": "OPEN",
            "author": payload.get("author", "EarthScape Analyst"),
            "station_id": payload.get("station_id", "GLOBAL"),
            "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": payload.get("description", "")
        }
        tickets.insert(0, new_ticket)
        with open(TICKETS_FILE, "w", encoding="utf-8") as f:
            json.dump(tickets, f, indent=2)
        self._send_json({"status": "SUCCESS", "ticket": new_ticket})

    def handle_post_tickets_update(self, payload):
        ticket_id = payload.get("ticket_id")
        new_status = payload.get("status", "RESOLVED")
        if TICKETS_FILE.exists():
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                tickets = json.load(f)
            for t in tickets:
                if t["ticket_id"] == ticket_id:
                    t["status"] = new_status
            with open(TICKETS_FILE, "w", encoding="utf-8") as f:
                json.dump(tickets, f, indent=2)
            self._send_json({"status": "SUCCESS", "ticket_id": ticket_id, "new_status": new_status})
        else:
            self._send_json({"error": "No tickets found"}, status=404)

    def handle_get_system_health(self):
        cluster_state = self.hdfs.get_cluster_status()
        health = {
            "system_status": "OPERATIONAL",
            "uptime_pct": 99.98,
            "uptime_days": 184.5,
            "cpu_utilization_pct": round(random.uniform(22.0, 38.0), 1),
            "memory_utilization_pct": round(random.uniform(41.0, 54.0), 1),
            "hdfs_namenode_status": "ACTIVE_HEALTHY",
            "datanodes_online": 4,
            "total_datanodes": 4,
            "hdfs_used_storage_mb": cluster_state.get("used_storage_mb", 18.5),
            "hdfs_total_capacity_gb": cluster_state.get("total_capacity_gb", 2000),
            "last_backup_completed": pd.Timestamp.now().strftime("%Y-%m-%d 03:00:00 UTC"),
            "backup_retention_policy": "30-Day Rolling Georeplicated Snapshot"
        }
        self._send_json(health)

    def handle_get_models_summary(self):
        summary_file = MODEL_DIR / "models_evaluation_summary.json"
        if summary_file.exists():
            with open(summary_file, "r", encoding="utf-8") as f:
                summary = json.load(f)
        else:
            summary = {"error": "Models not yet trained"}
        self._send_json(summary)

    def handle_post_mapreduce_run(self, payload):
        job_id = payload.get("job_id", "job_temp_anomalies")
        zone_filter = payload.get("zone_filter", "ALL")
        try:
            report = self.mr_runner.run_job(job_id=job_id, zone_filter=zone_filter)
            self._send_json(report)
        except Exception as e:
            self._send_json({"status": "FAILED", "error": str(e)}, status=500)

    def handle_post_predict_forecast(self, payload):
        """
        Executes ML Climate Forecaster with custom scenario sliders and zone-specific baselines.
        """
        zone_id = payload.get("zone_id", "Z01")
        target_year = int(payload.get("target_year", 2035))
        co2_scenario = float(payload.get("co2_scenario_ppm", 450.0))

        zone_info = next((z for z in CLIMATE_ZONES if z["zone_id"] == zone_id), CLIMATE_ZONES[0])
        base_temp = zone_info["base_temp"]
        warming_rate = zone_info["warming_rate"]
        climate_type = zone_info["climate_type"]

        model = self.get_model("temp_forecaster")
        if model is None:
            self._send_json({"error": "Forecaster model not found. Train models first."}, status=500)
            return

        dates = pd.date_range(start="2026-01-01", end=f"{target_year}-12-31", freq="MS")
        future_rows = []
        for dt in dates:
            doy = dt.dayofyear
            year_offset = (dt.year - 2015) + (doy / 365.25)
            co2_forcing = (co2_scenario - 400.0) * 0.035
            
            hemisphere_factor = 1.0 if zone_info["lat"] >= 0 else -1.0
            seasonal_amp = 12.0 * hemisphere_factor * np.sin(2 * np.pi * (doy - 80) / 365.25)
            if "Polar" in climate_type:
                seasonal_amp *= 1.6
            elif "Tropical" in climate_type:
                seasonal_amp *= 0.25

            projected_surface = base_temp + seasonal_amp + (warming_rate * year_offset) + co2_forcing

            future_rows.append({
                "timestamp": dt,
                "year": dt.year,
                "month": dt.month,
                "zone_id": zone_id,
                "surface_temp_c": round(projected_surface, 2),
                "co2_ppm": co2_scenario,
                "ch4_ppb": 1950.0 + (year_offset * 9.0),
                "solar_irradiance_wm2": 260.0,
                "humidity_pct": 60.0,
                "pressure_hpa": 1012.0,
                "aerosol_optical_depth": 0.18
            })
        df_future = pd.DataFrame(future_rows)
        fe_future = engineer_climate_features(df_future)

        feature_cols = [
            "zone_id", "trend_index", "sin_day", "cos_day",
            "co2_ppm", "ch4_ppb", "solar_irradiance_wm2",
            "humidity_pct", "pressure_hpa", "aerosol_optical_depth",
            "temp_lag_7d", "temp_lag_30d", "temp_rolling_mean_30d"
        ]

        predictions = model.predict(fe_future[feature_cols])

        fe_future["predicted_temp_c"] = predictions
        yearly = fe_future.groupby("year")["predicted_temp_c"].mean().reset_index()

        delta = round(float(yearly["predicted_temp_c"].iloc[-1] - yearly["predicted_temp_c"].iloc[0]), 2)

        output = {
            "zone_id": zone_id,
            "zone_name": zone_info["name"],
            "target_year": target_year,
            "co2_scenario_ppm": co2_scenario,
            "timeline_years": yearly["year"].tolist(),
            "predicted_mean_temps_c": [round(float(x), 2) for x in yearly["predicted_temp_c"].tolist()],
            "confidence_upper_c": [round(float(x) + 0.85, 2) for x in yearly["predicted_temp_c"].tolist()],
            "confidence_lower_c": [round(float(x) - 0.85, 2) for x in yearly["predicted_temp_c"].tolist()],
            "net_warming_projected_c": delta
        }
        self._send_json(output)

    def handle_post_predict_anomaly(self, payload):
        model = self.get_model("anomaly_detector")
        if model is None:
            self._send_json({"error": "Anomaly detector model not found."}, status=500)
            return

        input_df = pd.DataFrame([{
            "surface_temp_c": float(payload.get("surface_temp_c", 25.0)),
            "precipitation_mm": float(payload.get("precipitation_mm", 0.0)),
            "humidity_pct": float(payload.get("humidity_pct", 55.0)),
            "pressure_hpa": float(payload.get("pressure_hpa", 1012.0)),
            "wind_speed_kmh": float(payload.get("wind_speed_kmh", 15.0)),
            "solar_irradiance_wm2": float(payload.get("solar_irradiance_wm2", 280.0)),
            "co2_ppm": float(payload.get("co2_ppm", 420.0)),
            "aerosol_optical_depth": float(payload.get("aerosol_optical_depth", 0.15))
        }])

        is_anomaly, scores = predict_anomalies(model, input_df)
        is_anom_val = bool(is_anomaly[0] == 1)
        score_val = float(scores[0])

        classification = "CRITICAL_ANOMALY" if score_val > 70.0 else ("MODERATE_ANOMALY" if is_anom_val else "NORMAL_BASELINE")

        response = {
            "is_anomaly": is_anom_val,
            "anomaly_score_index": score_val,
            "classification": classification,
            "confidence_pct": round(min(99.0, max(50.0, 50.0 + score_val * 0.49)), 1),
            "input_metrics": payload
        }
        self._send_json(response)

    def handle_post_predict_impact(self, payload):
        model = self.get_model("impact_model")
        if model is None:
            self._send_json({"error": "Impact model not found."}, status=500)
            return

        input_df = pd.DataFrame([{
            "co2_ppm": float(payload.get("co2_ppm", 430.0)),
            "ch4_ppb": float(payload.get("ch4_ppb", 1920.0)),
            "global_deforestation_rate_mha": float(payload.get("global_deforestation_rate_mha", 11.5)),
            "fossil_fuel_emissions_gtco2": float(payload.get("fossil_fuel_emissions_gtco2", 34.0)),
            "arctic_sea_ice_extent_mkm2": float(payload.get("arctic_sea_ice_extent_mkm2", 4.2))
        }])

        pred_risk = float(model.predict(input_df[IMPACT_FEATURES])[0])
        risk_score = round(min(100.0, max(0.0, pred_risk)), 1)

        tier = "EXTREME_VULNERABILITY" if risk_score > 75 else ("HIGH_RISK" if risk_score > 50 else ("MODERATE_RISK" if risk_score > 25 else "STABLE"))

        response = {
            "climate_vulnerability_index": risk_score,
            "vulnerability_tier": tier,
            "extreme_event_multiplier": round(1.0 + (risk_score / 35.0), 2),
            "sea_level_rise_trajectory_cm_decade": round(3.5 * (risk_score / 45.0), 1),
            "input_parameters": payload
        }
        self._send_json(response)


def run_server(port: int = PORT):
    os.chdir(PROJECT_ROOT)

    # Initialize database and seed demo accounts before starting HTTP server
    print("[Server] Initializing database...")
    user_db.init_and_seed()

    handler = EarthScapeAPIHandler
    handler.hdfs.scan_and_register_blocks()
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", port), handler) as httpd:
        print(f"===========================================================")
        print(f" EarthScape Climate Agency Portal is LIVE on http://localhost:{port}")
        print(f"===========================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    run_server()
