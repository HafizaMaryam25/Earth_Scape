"""
EarthScape Climate Agency - eProject Report Diagram Generator (v2)
Generates DFDs, flowcharts, process and database-design diagrams as PNG images.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams")
os.makedirs(OUT, exist_ok=True)

C_PROC = "#dbeafe"; C_PROC_EC = "#1d4ed8"
C_STORE = "#fef3c7"; C_STORE_EC = "#b45309"
C_ENT = "#d1fae5"; C_ENT_EC = "#047857"
C_TERM = "#1e293b"; C_FLOW = "#334155"
C_DEC = "#fde68a"; C_DEC_EC = "#b45309"
C_ACC = "#ede9fe"; C_ACC_EC = "#6d28d9"
C_NOTE = "#f1f5f9"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

def new_fig(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=170)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax

def box(ax, cx, cy, w, h, text, fc, ec, fs=9.5, bold=True, tc="#0f172a", lw=1.6):
    p = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                       boxstyle="round,pad=0.35,rounding_size=1.6",
                       fc=fc, ec=ec, lw=lw, zorder=3)
    ax.add_patch(p)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, zorder=4, linespacing=1.35)

def store(ax, cx, cy, w, h, text, fs=8.6):
    x0, y0 = cx - w/2, cy - h/2
    ax.plot([x0 + 2.0, x0 + w], [y0 + h, y0 + h], color=C_STORE_EC, lw=1.6, zorder=3)
    ax.plot([x0, x0 + w], [y0, y0], color=C_STORE_EC, lw=1.6, zorder=3)
    ax.plot([x0 + w, x0 + w], [y0, y0 + h], color=C_STORE_EC, lw=1.6, zorder=3)
    ax.text(cx + 0.8, cy, text, ha="center", va="center", fontsize=fs,
            fontweight="bold", color="#0f172a", zorder=4, linespacing=1.3)

def diamond(ax, cx, cy, w, h, text, fs=8.6):
    xs = [cx, cx + w/2, cx, cx - w/2]; ys = [cy + h/2, cy, cy - h/2, cy]
    ax.fill(xs, ys, fc=C_DEC, ec=C_DEC_EC, lw=1.6, zorder=3)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, fontweight="bold", color="#0f172a", zorder=4)

def arrow(ax, x1, y1, x2, y2, label=None, fs=8.0, lx=0, ly=0, curved=0.0,
          color=C_FLOW, lw=1.5, dashed=False, two_way=False):
    style = "<|-|>" if two_way else "-|>"
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=13,
                        color=color, lw=lw, zorder=2,
                        linestyle=(0, (5, 3)) if dashed else "solid",
                        connectionstyle=f"arc3,rad={curved}")
    ax.add_patch(a)
    if label:
        ax.text((x1 + x2)/2 + lx, (y1 + y2)/2 + ly, label, fontsize=fs, color=C_FLOW,
                ha="center", va="center", zorder=5,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.92))

def note(ax, x, y, text, fs=7.8, ha="center"):
    ax.text(x, y, text, fontsize=fs, color="#475569", ha=ha, va="center", style="italic",
            bbox=dict(fc=C_NOTE, ec="#cbd5e1", boxstyle="round,pad=0.45", lw=0.9), zorder=5)

def title(ax, t, sub=None):
    ax.text(50, 97.6, t, ha="center", va="top", fontsize=13.5, fontweight="bold", color="#0f172a")
    if sub:
        ax.text(50, 93.9, sub, ha="center", va="top", fontsize=9, color="#475569")

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)

# ============================================================== 1. DFD LEVEL 0
fig, ax = new_fig(11.5, 7.4)
title(ax, "Data Flow Diagram - Level 0 (Context Diagram)",
      "EarthScape Climate Agency - complete platform boundary")

c = Circle((50, 48), 13.5, fc=C_PROC, ec=C_PROC_EC, lw=2, zorder=3)
ax.add_patch(c)
ax.text(50, 48, "0\nEarthScape\nClimate Agency\nPlatform", ha="center", va="center",
        fontsize=11, fontweight="bold", color="#0f172a", zorder=4)

box(ax, 13, 78, 22, 12, "Climate Analyst\n(Role: analyst)", C_ENT, C_ENT_EC)
box(ax, 13, 18, 22, 12, "Administrator\n(Role: admin)", C_ENT, C_ENT_EC)
box(ax, 86, 18, 23, 12, "Weather Stations &\nIoT Sensor Network", C_ENT, C_ENT_EC)
box(ax, 86, 78, 23, 12, "SQL Server LocalDB\n(Identity Store)", C_ACC, C_ACC_EC)

arrow(ax, 24.5, 72.5, 38.5, 56.5, "login / register\ncredentials", lx=-2, ly=3)
arrow(ax, 36.5, 50.5, 22.5, 66.5, "session token,\nrole, analytics\n& ML results", lx=-5, ly=-4)
arrow(ax, 24.5, 23.5, 38.5, 39.5, "admin commands\n(ticket resolve)", lx=-3, ly=-3.5)
arrow(ax, 74.5, 40, 86, 24.5, "telemetry\npackets", lx=4, ly=1)
arrow(ax, 74.5, 55.5, 86, 71.5, None, two_way=True, lw=1.7)
ax.text(81.5, 63.5, "SQL queries  /  user\nrecords + bcrypt hashes", fontsize=8, color=C_FLOW,
        ha="center", zorder=5, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.92))
save(fig, "dfd_level0.png")

# ============================================================== 2. DFD LEVEL 1
fig, ax = new_fig(14, 8.8)
title(ax, "Data Flow Diagram - Level 1",
      "Main processes, data stores and flows of the EarthScape platform")

# external entities
box(ax, 12, 88, 17, 8, "Climate\nAnalyst", C_ENT, C_ENT_EC)
box(ax, 12, 8, 17, 8, "Administrator", C_ENT, C_ENT_EC)
box(ax, 88, 88, 19, 8, "Weather Stations\n& IoT Sensors", C_ENT, C_ENT_EC)

# processes
box(ax, 32, 72, 22, 9, "1.0\nAuthenticate User", C_PROC, C_PROC_EC)
box(ax, 68, 72, 24, 9, "2.0\nIngest, Clean & Partition\nClimate Data", C_PROC, C_PROC_EC, fs=8.4)
box(ax, 32, 50, 22, 10, "5.0\nGenerate Alerts from\nThresholds", C_PROC, C_PROC_EC, fs=8.4)
box(ax, 68, 52, 24, 10, "3.0\nExecute MapReduce\nBatch Jobs", C_PROC, C_PROC_EC, fs=8.4)
box(ax, 68, 30, 24, 10, "4.0\nRun ML Inference\n(forecast / anomaly / impact)", C_PROC, C_PROC_EC, fs=8.2)
box(ax, 32, 26, 22, 10, "6.0\nManage Support\nTickets", C_PROC, C_PROC_EC, fs=8.4)

# data stores
store(ax, 50, 88, 20, 7, "D1\nUsers (SQL Server\nEarthScapeDb)")
store(ax, 93, 66, 13, 8, "D2\nHDFS\nPartitions")
store(ax, 93, 48, 13, 8, "D3\nMR Job\nResults")
store(ax, 93, 12, 13, 8, "D6\nModel\nArtifacts")
store(ax, 32, 37.5, 18, 6.5, "D4\nAlert Config")
store(ax, 32, 13, 18, 6.5, "D5\nSupport Tickets")

# flows
arrow(ax, 16, 84, 25, 76.5, "credentials", lx=-3.5, ly=1)
arrow(ax, 24, 69, 15.5, 81, "token + role", lx=-4, ly=-1, curved=0.25)
arrow(ax, 37, 76.5, 42, 84.5, "SQL queries /\nuser records", lx=-4.5, ly=0.5)
arrow(ax, 82, 84, 74, 76.5, "telemetry\npackets", lx=3, ly=1.5)
arrow(ax, 80, 72, 87, 68, "partitioned\nblocks", lx=1.5, ly=2.5)
arrow(ax, 68, 67.5, 68, 57.5, "input blocks")
arrow(ax, 80, 52, 87, 49, "job results", lx=1, ly=2)
arrow(ax, 58, 68, 50, 55.5, "recent climate\ndata", lx=-5, ly=1)
arrow(ax, 50, 67.5, 50, 35.5, "cleaned dataset\n(training / inference)", lx=-9, ly=0)
arrow(ax, 68, 47, 68, 35.5, "aggregated\nfeatures", lx=6, ly=0)
arrow(ax, 76, 26, 88, 15.5, "trained model\nfiles (.joblib)", lx=4, ly=2)
arrow(ax, 32, 45, 32, 41, "thresholds")
arrow(ax, 32, 21, 32, 16.5, "tickets")
arrow(ax, 18, 12, 24, 21.5, "ticket resolve\n(admin only)", lx=-6, ly=-1)
arrow(ax, 20, 86, 57, 59, "protected requests: run jobs / predictions /\nalerts config (Bearer token)", lx=-6, ly=7, curved=-0.18, dashed=True)
arrow(ax, 57, 56, 22, 83, "job reports / predictions", lx=8, ly=4, curved=-0.18, dashed=True)
note(ax, 32, 2.5, "Ticket creation: any authenticated user  |  Ticket resolution: Administrator only")
save(fig, "dfd_level1.png")

# ============================================================== 3. ARCHITECTURE
fig, ax = new_fig(12.8, 8.4)
title(ax, "System Architecture / Process Diagram",
      "Layered pipeline from raw climate sources to the web dashboard")

layers = [
    ("PRESENTATION", ["Web Dashboard\n(8-tab SPA)", "Chart.js Charts", "Leaflet GIS Map", "Live Telemetry\nFeed"], "#e0f2fe", "#0369a1"),
    ("APPLICATION", ["server.py\nREST API + RBAC", "db.py\nAuth + bcrypt", "Alert Engine", "Ticket Service"], "#dbeafe", "#1d4ed8"),
    ("INTELLIGENCE", ["Gradient Boosting\nTemp Forecaster", "Isolation Forest\nAnomaly Detector", "Random Forest\nImpact Regressor"], "#ede9fe", "#6d28d9"),
    ("BATCH PROCESSING", ["MR Job Runner", "Temp Anomaly Job", "GHG Emissions Job", "Extreme Events Job"], "#fef3c7", "#b45309"),
    ("DISTRIBUTED STORAGE", ["HDFS NameNode\n(simulated)", "4 DataNodes\n3x Replication", "110 Zone/Year\nPartition Blocks"], "#d1fae5", "#047857"),
    ("INGESTION", ["CSV/JSON\nLoaders", "Cleaning &\nImputation", "Zone/Year\nPartitioning"], "#fce7f3", "#be185d"),
    ("DATA SOURCES", ["climate_historical_daily.csv\n(40,180 records)", "GHG emissions\n(312 records)", "Stations / Zones\nJSON + sensor stream\n(500 packets)"], "#f1f5f9", "#475569"),
]
ys = [86, 72.5, 59, 45.5, 32, 18.5, 5]
for (label, items, fc, ec), cy in zip(layers, ys):
    ax.text(1.2, cy + 5.0, label, ha="left", va="center", fontsize=8.2, fontweight="bold", color=ec)
    n = len(items)
    total_w = 75; gap = 3
    w = (total_w - gap * (n - 1)) / n
    x0 = 11.5
    for i, it in enumerate(items):
        cx = x0 + w/2 + i * (w + gap)
        box(ax, cx, cy, w - 1.5, 9.5, it, fc, ec, fs=7.7)
for i in range(len(ys) - 1):
    y1 = ys[i] - 5.4; y2 = ys[i + 1] + 5.4
    for fx in (32, 62):
        arrow(ax, fx, y1 - 0.4, fx, y2 + 0.4, lw=1.7)
box(ax, 94.5, 72.5, 10, 16, "SQL Server\nLocalDB\n\nUsers &\nroles only", C_ACC, C_ACC_EC, fs=7.6)
arrow(ax, 94.5, 64.2, 90.5, 68, lw=1.3, dashed=True, lx=3)
save(fig, "architecture_diagram.png")

# ============================================================== 4. PIPELINE FLOWCHART
fig, ax = new_fig(9.6, 12.6)
title(ax, "End-to-End Data Pipeline Flowchart")
box(ax, 50, 90, 26, 6, "START", C_TERM, C_TERM, tc="white")
diamond(ax, 50, 78, 34, 13, "Raw datasets exist in\ndata/raw ?")
box(ax, 15, 62, 26, 10, "Generate synthetic\nclimate datasets\n(generator.py)", C_PROC, C_PROC_EC, fs=8.6)
box(ax, 50, 62, 28, 10, "Load & validate CSV/JSON\nsources (ingestion.py)", C_PROC, C_PROC_EC, fs=8.6)
box(ax, 50, 49, 28, 9, "Clean, impute & normalize\nmissing values", C_PROC, C_PROC_EC, fs=8.6)
box(ax, 50, 36, 28, 9, "Save climate_master_cleaned.csv\n+ write HDFS zone/year blocks", C_PROC, C_PROC_EC, fs=8.4)
box(ax, 50, 23, 28, 9, "Register blocks: checksums,\n3x replica placement (hdfs_manager)", C_PROC, C_PROC_EC, fs=8.2)
box(ax, 50, 10.5, 28, 9, "Run MapReduce jobs +\nserve ML inference via REST API", C_PROC, C_PROC_EC, fs=8.6)
box(ax, 50, 2.2, 22, 4.4, "END", C_TERM, C_TERM, tc="white", fs=9)
arrow(ax, 50, 87, 50, 84.5)
arrow(ax, 50, 71.5, 50, 67, "yes")
arrow(ax, 33, 78, 21, 67, "no", lx=-3)
arrow(ax, 28, 62, 36, 62)
arrow(ax, 50, 57, 50, 53.5)
arrow(ax, 50, 44.5, 50, 40.5)
arrow(ax, 50, 31.5, 50, 27.5)
arrow(ax, 50, 18.5, 50, 15)
arrow(ax, 50, 6, 50, 4.4)
save(fig, "flowchart_pipeline.png")

# ============================================================== 5. MAPREDUCE FLOW
fig, ax = new_fig(10.5, 7.4)
title(ax, "MapReduce Job Execution Flowchart",
      "Example: Temperature Anomaly & Baseline Analysis (job_temp_anomalies)")
box(ax, 16, 82, 26, 10, "INPUT\n110 HDFS partition blocks\n(zone=ZXX / climate_data_YYYY.csv)", C_ENT, C_ENT_EC, fs=8.2)
box(ax, 16, 60, 26, 12, "SPLIT & MAP\nTemperatureAnomalyMapper\nemits key=(zone#month)\nvalue=(temp, year, timestamp)", C_PROC, C_PROC_EC, fs=8.2)
box(ax, 50, 60, 22, 12, "SHUFFLE & SORT\ngroup intermediate\nvalues by key", C_PROC, C_PROC_EC, fs=8.4)
box(ax, 82, 60, 26, 12, "REDUCE\nTemperatureAnomalyReducer\ncomputes climatology means,\nstd-dev & yearly anomalies", C_PROC, C_PROC_EC, fs=8.0)
box(ax, 82, 34, 26, 11, "OUTPUT\nmr_temp_anomalies_output.json\n+ execution telemetry", C_STORE, C_STORE_EC, fs=8.2)
box(ax, 46, 34, 24, 11, "Job Runner\nrecords timing, throughput,\nmapper/reducer task counts", C_ACC, C_ACC_EC, fs=8.2)
box(ax, 16, 34, 24, 11, "REST API\nPOST /api/mapreduce/run\n(Analyst+ role)", C_ENT, C_ENT_EC, fs=8.2)
arrow(ax, 16, 77, 16, 66)
arrow(ax, 29, 60, 39, 60)
arrow(ax, 61, 60, 69, 60)
arrow(ax, 82, 54, 82, 39.5)
arrow(ax, 69, 34, 58, 34, dashed=True)
arrow(ax, 28, 34, 40, 55, "trigger", curved=0.15)
ax.text(50, 12, "The same pattern runs for GHG Emissions (key=year) and Extreme Events (key=zone#event_type).",
        ha="center", fontsize=8.4, color="#475569", style="italic")
save(fig, "flowchart_mapreduce.png")

# ============================================================== 6. AUTH FLOW
fig, ax = new_fig(8.6, 12.4)
title(ax, "Login / Authentication Flowchart")
box(ax, 50, 90, 30, 6, "START", C_TERM, C_TERM, tc="white")
box(ax, 50, 81, 34, 8, "Enter email + password\nPOST /api/auth/login", C_PROC, C_PROC_EC, fs=8.8)
diamond(ax, 50, 68, 36, 14, "User found in SQL Server\nEarthScapeDb.Users ?")
diamond(ax, 50, 51, 36, 14, "bcrypt.checkpw()\nhash match ?")
box(ax, 50, 37, 34, 9, "Generate 40-char SHA-256\nsession token, store in\nactive_sessions", C_PROC, C_PROC_EC, fs=8.4)
box(ax, 50, 24, 34, 9, "Return token + role;\nfrontend stores Bearer token", C_PROC, C_PROC_EC, fs=8.6)
diamond(ax, 50, 10.5, 38, 12, "Role level >= required\nfor protected endpoint ?")
box(ax, 88, 10.5, 20, 9, "Execute protected\noperation (200)", C_ENT, C_ENT_EC, fs=8.2)
box(ax, 12, 10.5, 20, 9, "403 Permission\ndenied", "#fee2e2", "#b91c1c", fs=8.2)
arrow(ax, 50, 87, 50, 85)
arrow(ax, 50, 77, 50, 75)
arrow(ax, 50, 61, 50, 58, "yes")
arrow(ax, 68, 68, 93, 68, "no", ly=1.6)
arrow(ax, 93, 68, 93, 81)
arrow(ax, 93, 81, 67, 81, "401 Invalid credentials", ly=1.8)
arrow(ax, 50, 44, 50, 41.5, "yes")
arrow(ax, 68, 51, 90, 51, "no", ly=1.6)
arrow(ax, 90, 51, 90, 64, curved=0.25, dashed=True)
arrow(ax, 50, 32.5, 50, 28.5)
arrow(ax, 50, 19.5, 50, 16.5)
arrow(ax, 69, 10.5, 78, 10.5, "yes")
arrow(ax, 31, 10.5, 22, 10.5, "no")
save(fig, "flowchart_authentication.png")

# ============================================================== 7. ALERT FLOW
fig, ax = new_fig(10.5, 11.6)
title(ax, "Automated Alert Generation Flowchart")
box(ax, 50, 90, 30, 6, "START  (GET /api/alerts)", C_TERM, C_TERM, tc="white", fs=9)
box(ax, 50, 81.5, 36, 8, "Load alert thresholds from\nalerts_config.json", C_STORE, C_STORE_EC, fs=8.6)
box(ax, 50, 72.5, 36, 8, "Load recent 20% of climate records\n+ latest GHG values + stations", C_PROC, C_PROC_EC, fs=8.4)
diamond(ax, 50, 60, 40, 14, "Per zone: max temp, max wind,\nmin pressure vs thresholds ?")
diamond(ax, 50, 44, 38, 13, "Arctic anomaly (Z01) >\ntemp_arctic_anomaly_c ?")
diamond(ax, 50, 29.5, 38, 13, "Latest CO2 > co2_critical_ppm\nor 24h precipitation > 75 mm ?")
box(ax, 50, 16, 38, 9, "Emit alert objects with severity\nCRITICAL / HIGH / MODERATE", C_PROC, C_PROC_EC, fs=8.4)
box(ax, 50, 6, 34, 7, "Sort by severity, keep top 10,\nreturn JSON to dashboard", C_PROC, C_PROC_EC, fs=8.4)
arrow(ax, 50, 87, 50, 85.5)
arrow(ax, 50, 77.5, 50, 76.5)
arrow(ax, 50, 68.5, 50, 67)
arrow(ax, 50, 53, 50, 50.5, "breach")
arrow(ax, 30, 60, 8, 60, "within limits", ly=1.8)
arrow(ax, 50, 37.5, 50, 36, "breach")
arrow(ax, 30, 44, 8, 44, "no", ly=1.4)
arrow(ax, 50, 23, 50, 20.5, "breach")
arrow(ax, 30, 29.5, 8, 29.5, "no", ly=1.4)
arrow(ax, 8, 60, 8, 29.5, dashed=True)
arrow(ax, 8, 29.5, 28, 18, "no alerts", curved=0.1, dashed=True)
arrow(ax, 50, 11.5, 50, 9.5)
save(fig, "flowchart_alerts.png")

# ============================================================== 8. DATABASE DESIGN
fig, ax = new_fig(13, 8.2)
title(ax, "Database Design / Storage Structure",
      "Relational identity store (SQL Server) separated from analytical file storage")

ax.text(23, 89.5, "EARTHSCAPEDb - Users Table (SQL Server LocalDB)", ha="center",
        fontsize=10, fontweight="bold", color=C_ACC_EC)
cols = [("Id", "INT IDENTITY(1,1)", "PRIMARY KEY"),
        ("Name", "NVARCHAR(200)", "NOT NULL"),
        ("Email", "NVARCHAR(320)", "NOT NULL - UNIQUE INDEX UQ_Users_Email"),
        ("PasswordHash", "NVARCHAR(200)", "NOT NULL (bcrypt)"),
        ("Role", "NVARCHAR(50)", "NOT NULL DEFAULT 'analyst'"),
        ("CreatedAt", "NVARCHAR(50)", "NOT NULL (UTC)")]
x0, y0, w = 4.5, 84, 37
row_h = 5.6
th = row_h * (len(cols) + 1.0)
ax.add_patch(FancyBboxPatch((x0, y0 - th), w, th, boxstyle="round,pad=0.3,rounding_size=1.2",
                            fc="white", ec=C_ACC_EC, lw=1.8, zorder=3))
ax.add_patch(FancyBboxPatch((x0, y0 - row_h * 0.95), w, row_h * 0.95,
                            boxstyle="round,pad=0.3,rounding_size=1.2", fc=C_ACC, ec=C_ACC_EC, lw=1.8, zorder=4))
ax.text(x0 + w/2, y0 - row_h * 0.48, "USERS", ha="center", fontsize=9.5, fontweight="bold", zorder=5)
for i, (cname, ctype, ccon) in enumerate(cols):
    ry = y0 - row_h * (i + 1.5)
    ax.text(x0 + 1.3, ry, cname, fontsize=8.2, fontweight="bold", va="center", zorder=5,
            color="#b91c1c" if "PK" in ccon else "#0f172a")
    ax.text(x0 + 9.3, ry, ctype, fontsize=7.8, va="center", zorder=5, color="#334155")
    ax.text(x0 + 20.5, ry, ccon, fontsize=6.9, va="center", zorder=5, color="#64748b")
    ax.plot([x0 + 0.6, x0 + w - 0.6], [ry - row_h/2, ry - row_h/2], color="#e2e8f0", lw=0.8, zorder=4)
ax.text(23, y0 - th - 5.5,
        "Roles:  Administrator (level 2)  /  Climate Analyst (level 1)\n"
        "Unique index UQ_Users_Email prevents duplicate accounts.\n"
        "Demo seed on first start: 1 Admin + 3 Analysts.",
        ha="center", fontsize=8.2, color="#475569", linespacing=1.6,
        bbox=dict(fc=C_NOTE, ec="#cbd5e1", boxstyle="round,pad=0.55"))

ax.text(72, 89.5, "ANALYTICAL DATA - FILE / PARTITION STORES (not in SQL Server)",
        ha="center", fontsize=10, fontweight="bold", color=C_STORE_EC)
stores = [
    ("data/raw/", "climate_historical_daily.csv (40,180 rec)\ngreenhouse_gases_emissions.csv (312 rec)\nweather_stations.json (10) | climate_zones.json (10)\nsensor_stream_sample.json (500 packets)", 73),
    ("data/processed/", "climate_master_cleaned.csv | ingestion_metadata.json\nhdfs_cluster_state.json | hdfs_partition_manifest.json\nalerts_config.json | support_tickets.json", 54),
    ("data/processed/hdfs_partitions/", "110 blocks:  zone=ZXX/climate_data_YYYY.csv\n10 zones x 11 years (2015-2025)\n4 DataNodes - replication factor 3", 35),
    ("data/processed/mr_results/ + models/", "mr_*_output.json + job_*_latest_execution.json\ntemp_forecaster.joblib | anomaly_detector.joblib\nimpact_model.joblib + evaluation JSON reports", 16),
]
for head, body, cy in stores:
    ax.text(50.5, cy + 8.0, head, fontsize=8.8, fontweight="bold", color="#0f172a", ha="left", va="center")
    ax.text(50.5, cy - 1.2, body, fontsize=7.6, color="#334155", ha="left", va="top", linespacing=1.65,
            bbox=dict(fc="#fffbeb", ec=C_STORE_EC, boxstyle="round,pad=0.5", lw=1.2))
save(fig, "db_design.png")

print("ALL DIAGRAMS DONE")
