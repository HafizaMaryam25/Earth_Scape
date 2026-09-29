/**
 * EarthScape Climate Agency - Interactive Command Center Application Logic
 */

// Application State
const state = {
    activeTab: 'vitals',
    currentRole: 'admin', // admin | analyst
    authToken: null,
    userSession: null,
    stations: [],
    zones: [],
    streamingActive: true,
    streamTimer: null,
    charts: {
        historical: null,
        ghg: null,
        forecast: null,
        stream: null
    },
    map: null,
    mapMarkers: []
};

// Authenticated fetch helper - includes token in headers
async function authFetch(url, options = {}) {
    const headers = options.headers || {};
    if (state.authToken) {
        headers['Authorization'] = `Bearer ${state.authToken}`;
    }
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }
    return fetch(url, { ...options, headers });
}

// =========================================================================
// Initialization
// =========================================================================
document.addEventListener('DOMContentLoaded', async () => {
    lucide.createIcons();
    initClock();
    // Show login screen; after login, initialize dashboard
    document.getElementById('login-overlay').style.display = 'flex';
});

// Called after successful authentication
async function initializeDashboard() {
    document.getElementById('login-overlay').style.display = 'none';
    document.getElementById('app-layout').style.display = 'flex';
    loadGlobalVitals();
    loadZonesTable();
    loadZonesAndStations();
    initHistoricalChart();
    initGHGChart();
    initLeafletMap();
    initForecastChart();
    initStreamChart();
    loadAlerts();
    loadAlertConfig();
    loadTickets();
    loadSystemHealth();
    startStreaming();
    lucide.createIcons();
}

// Handle login form submission
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (data.token) {
            state.authToken = data.token;
            state.userSession = data;
            state.currentRole = data.role;
            errorEl.style.display = 'none';
            applyRoleUI(data);
            await initializeDashboard();
        } else {
            errorEl.textContent = data.error || 'Login failed';
            errorEl.style.display = 'block';
        }
    } catch (err) {
        errorEl.textContent = 'Connection error. Is the server running?';
        errorEl.style.display = 'block';
    }
}

// Handle analyst registration
async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const errorEl = document.getElementById('register-error');

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, display_name: name })
        });
        const data = await res.json();
        if (data.token) {
            state.authToken = data.token;
            state.userSession = data;
            state.currentRole = data.role;
            errorEl.style.display = 'none';
            applyRoleUI(data);
            await initializeDashboard();
        } else {
            errorEl.textContent = data.error || 'Registration failed';
            errorEl.style.display = 'block';
        }
    } catch (err) {
        errorEl.textContent = 'Connection error. Is the server running?';
        errorEl.style.display = 'block';
    }
}

// Toggle between login and register forms
function showRegisterForm() {
    document.getElementById('login-form').style.display = 'none';
    document.querySelector('.login-switch').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.getElementById('register-switch').style.display = 'block';
    document.getElementById('login-error').style.display = 'none';
}

function showLoginForm() {
    document.getElementById('login-form').style.display = 'block';
    document.querySelector('.login-switch').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('register-switch').style.display = 'none';
    document.getElementById('register-error').style.display = 'none';
}

// Apply role-based UI after login/register
function applyRoleUI(data) {
    const role = data.role;
    // Update role badge
    const badge = document.getElementById('active-role-badge');
    if (badge) {
        badge.className = 'badge';
        if (role === 'admin') {
            badge.classList.add('badge-admin');
            badge.textContent = 'Administrator';
        } else {
            badge.classList.add('badge-analyst');
            badge.textContent = 'Climate Analyst';
        }
    }
    // Show user email in sidebar
    const emailDisplay = document.getElementById('user-email-display');
    if (emailDisplay) emailDisplay.textContent = data.email;

    // Analysts cannot resolve tickets (admin-only)
    state.currentRole = role;
}

// Handle logout
async function handleLogout() {
    try {
        await authFetch('/api/auth/logout', { method: 'POST' });
    } catch (err) { /* ignore */ }
    state.authToken = null;
    state.userSession = null;
    if (state.streamTimer) clearInterval(state.streamTimer);
    document.getElementById('app-layout').style.display = 'none';
    document.getElementById('login-overlay').style.display = 'flex';
    document.getElementById('login-password').value = '';
}

// Real-time UTC Clock
function initClock() {
    setInterval(() => {
        const now = new Date();
        const clockEl = document.getElementById('live-clock');
        if (clockEl) {
            clockEl.textContent = 'UTC ' + now.toUTCString().split(' ')[4];
        }
    }, 1000);
}

// =========================================================================
// Navigation
// =========================================================================
function switchTab(tabId) {
    state.activeTab = tabId;

    // Update Nav Buttons
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    const activeNav = document.getElementById(`nav-${tabId}`);
    if (activeNav) activeNav.classList.add('active');

    // Update Tab Panes
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
    const targetPane = document.getElementById(`tab-${tabId}`);
    if (targetPane) targetPane.classList.add('active');

    // Update Header Title
    const titles = {
        'vitals': { title: 'Global Climate Vital Signs', desc: 'Synchronous multi-sensor telemetry, satellite observations, and long-term anomalies' },
        'stations': { title: 'Weather Observation Network & GIS Map', desc: 'Real-time telemetry and metadata from 10 global meteorological hubs' },
        'mapreduce': { title: 'Hadoop HDFS & MapReduce Engine', desc: 'Distributed parallel batch analytics, baseline climatology, and risk indexing' },
        'ml-sandbox': { title: 'AI & Climate Prediction Sandbox', desc: 'Multi-scenario forecasting, anomaly detection, and empirical risk modeling' },
        'streaming': { title: 'Real-Time IoT Environmental Telemetry', desc: 'Live high-frequency sub-second sensor streams across global observation nodes' },
        'alerts': { title: 'Automated Early Warnings & Alerts', desc: 'Automated threshold-based triggers, heatwaves, cyclones, and critical CO2 breaches' },
        'tickets': { title: 'Support Desk & Incident Reporting', desc: 'Report field anomalies, submit feedback, or request custom data exports' },
        'system': { title: 'Cluster Infrastructure & Node Monitor', desc: 'HDFS block replication, CPU/Memory telemetry, and 99.98% SLA tracker' }
    };

    if (titles[tabId]) {
        document.getElementById('page-title').textContent = titles[tabId].title;
        document.getElementById('page-desc').textContent = titles[tabId].desc;
    }

    // Refresh layout-sensitive components
    if (tabId === 'stations' && state.map) {
        setTimeout(() => state.map.invalidateSize(), 200);
    }
    if (tabId === 'ml-sandbox' && !state.charts.forecast) {
        runMLForecast();
    }
    if (tabId === 'system') {
        loadSystemHealth();
    }
}

// changeRole removed — users cannot switch roles. Role is assigned at login/registration.

function refreshCurrentTab() {
    const icon = document.getElementById('refresh-icon');
    if (icon) icon.classList.add('rotating');

    loadGlobalVitals();
    loadZonesTable();
    loadZonesAndStations();
    loadHistoricalChart();
    loadAlerts();
    loadTickets();
    loadSystemHealth();

    setTimeout(() => {
        if (icon) icon.classList.remove('rotating');
    }, 600);
}

// =========================================================================
// TAB 1: Global Vitals & Charts
// =========================================================================
async function loadGlobalVitals() {
    try {
        const res = await fetch('/api/vitals');
        const data = await res.json();

        document.getElementById('kpi-temp-anom').textContent = `+${data.global_temp_anomaly_c} °C`;
        document.getElementById('kpi-co2').textContent = `${data.atmospheric_co2_ppm} ppm`;
        document.getElementById('kpi-sea-ice').textContent = `${data.arctic_sea_ice_mkm2} M km²`;
        document.getElementById('kpi-deforest').textContent = `${data.deforestation_rate_mha} M ha/yr`;
        document.getElementById('header-records').textContent = Number(data.total_ingested_records).toLocaleString();
        document.getElementById('nav-alert-counter').textContent = data.active_alerts_count;
    } catch (err) {
        console.error('Failed to load vitals:', err);
    }
}

async function loadZonesAndStations() {
    try {
        const res = await fetch('/api/stations');
        state.stations = await res.json();

        // Render Sidebar Station List
        renderStationList(state.stations);
        plotMapMarkers(state.stations);
    } catch (err) {
        console.error('Failed to load stations:', err);
    }
}

async function loadZonesTable() {
    try {
        const tbody = document.getElementById('zones-tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-dim" style="text-align:center;padding:20px;">Loading zone data...</td></tr>';
        }
        const res = await fetch('/api/zones');
        const zones = await res.json();
        state.zones = zones;

        if (tbody) {
            tbody.innerHTML = '';
            zones.forEach(z => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong class="text-cyan">${z.zone_id}</strong></td>
                    <td><strong>${z.name}</strong></td>
                    <td class="font-mono">${z.lat}°N, ${z.lon}°E</td>
                    <td><span class="badge badge-info">${z.climate_type}</span></td>
                    <td>${z.base_temp} °C</td>
                    <td><span class="text-crimson">+${z.warming_rate}°C/yr</span></td>
                    <td>${z.partition_blocks} Blocks</td>
                    <td><span class="badge badge-success">${z.status}</span></td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error('Failed to load zones:', err);
        const tbody = document.getElementById('zones-tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-crimson" style="text-align:center;padding:20px;">Failed to load zone data</td></tr>';
        }
    }
}

async function loadSystemHealth() {
    try {
        const res = await fetch('/api/system/health');
        const health = await res.json();

        const cpuEl = document.getElementById('sys-cpu');
        if (cpuEl) cpuEl.textContent = `${health.cpu_utilization_pct}%`;

        const memEl = document.getElementById('sys-mem');
        if (memEl) memEl.textContent = `${health.memory_utilization_pct}%`;

        const uptimeEl = document.getElementById('sys-uptime');
        if (uptimeEl) uptimeEl.textContent = `${health.uptime_pct}%`;

        const datanodesEl = document.getElementById('sys-datanodes');
        if (datanodesEl) datanodesEl.textContent = `${health.datanodes_online} / ${health.total_datanodes}`;

        const storageEl = document.getElementById('sys-storage-used');
        if (storageEl) storageEl.textContent = `${health.hdfs_used_storage_mb} MB Used`;

        const hdfsStatusEl = document.getElementById('sys-hdfs-status');
        if (hdfsStatusEl) hdfsStatusEl.textContent = health.hdfs_namenode_status;

        const backupEl = document.getElementById('sys-backup');
        if (backupEl) backupEl.textContent = health.last_backup_completed;
    } catch (err) {
        console.error('Failed to load system health:', err);
    }
}

function initHistoricalChart() {
    const ctx = document.getElementById('historicalChart').getContext('2d');
    state.charts.historical = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Mean Surface Temp (°C)',
                    data: [],
                    borderColor: '#00f0ff',
                    backgroundColor: 'rgba(0, 240, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y'
                },
                {
                    label: 'Atmospheric CO2 (ppm)',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [4, 4],
                    tension: 0.2,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } } }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', maxTicksLimit: 12 } },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#00f0ff' },
                    title: { display: true, text: 'Temperature (°C)', color: '#00f0ff' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#10b981' },
                    title: { display: true, text: 'CO2 (ppm)', color: '#10b981' }
                }
            }
        }
    });

    loadHistoricalChart();
}

async function loadHistoricalChart() {
    const zoneSelect = document.getElementById('vitals-zone-select');
    const zoneId = zoneSelect ? zoneSelect.value : 'ALL';
    try {
        const res = await fetch(`/api/historical?zone_id=${zoneId}`);
        const data = await res.json();

        if (state.charts.historical) {
            state.charts.historical.data.labels = data.labels;
            state.charts.historical.data.datasets[0].data = data.temperatures;
            state.charts.historical.data.datasets[1].data = data.co2;
            state.charts.historical.update();
        }
    } catch (err) {
        console.error('Failed to load historical chart:', err);
    }
}

async function initGHGChart() {
    const ctx = document.getElementById('ghgCompositionChart').getContext('2d');
    try {
        const res = await fetch('/api/ghg');
        const ghgData = await res.json();
        const recent = ghgData.slice(-36); // last 3 years

        state.charts.ghg = new Chart(ctx, {
            type: 'line',
            data: {
                labels: recent.map(d => d.date),
                datasets: [
                    {
                        label: 'CO2 (ppm)',
                        data: recent.map(d => d.co2_ppm),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'CH4 / 5 (ppb proxy)',
                        data: recent.map(d => d.ch4_ppb / 5.0),
                        borderColor: '#f59e0b',
                        borderWidth: 2,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#94a3b8', font: { size: 11 } } } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#64748b', maxTicksLimit: 6 } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
                }
            }
        });
    } catch (err) {
        console.error('Failed to init GHG chart:', err);
    }
}

function exportZoneDataCSV() {
    let csv = 'Zone ID,Station ID,Name,Latitude,Longitude,Current Temp C,Current CO2 ppm,Status\n';
    state.stations.forEach(s => {
        csv += `${s.zone_id},${s.station_id},"${s.name}",${s.lat},${s.lon},${s.current_temp_c || 0},${s.current_co2_ppm || 0},ACTIVE\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', 'earthscape_climate_zones.csv');
    a.click();
}

// =========================================================================
// TAB 2: Weather Stations & Geospatial Map
// =========================================================================
function initLeafletMap() {
    const mapContainer = document.getElementById('climate-map');
    if (!mapContainer) return;

    state.map = L.map('climate-map', {
        center: [20.0, 0.0],
        zoom: 2,
        zoomControl: true,
        minZoom: 1.5,
        maxZoom: 10
    });

    // Dark Tile Layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; EarthScape Agency',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(state.map);
}

function plotMapMarkers(stations) {
    if (!state.map) return;

    // Clear existing markers
    state.mapMarkers.forEach(m => state.map.removeLayer(m));
    state.mapMarkers = [];

    stations.forEach(st => {
        const temp = st.current_temp_c || 15.0;
        let color = '#10b981'; // Green (normal)
        if (temp < 0) color = '#00f0ff'; // Cyan (polar)
        else if (temp > 35) color = '#ef4444'; // Red (extreme)
        else if (temp > 25) color = '#f59e0b'; // Amber (warm)

        const circleMarker = L.circleMarker([st.lat, st.lon], {
            radius: 8,
            fillColor: color,
            color: '#ffffff',
            weight: 1.5,
            opacity: 0.9,
            fillOpacity: 0.85
        }).addTo(state.map);

        const popupContent = `
            <div style="font-family: 'Inter', sans-serif; min-width: 180px; color: #0f172a;">
                <h4 style="margin: 0 0 4px 0; font-size: 14px; font-weight: 700;">${st.name}</h4>
                <div style="font-size: 11px; color: #475569; margin-bottom: 6px;">ID: <strong>${st.station_id}</strong> (${st.zone_id})</div>
                <div style="font-size: 12px; margin-bottom: 2px;">Surface Temp: <strong style="color: ${color};">${st.current_temp_c || 'N/A'} °C</strong></div>
                <div style="font-size: 12px; margin-bottom: 2px;">Atmospheric CO2: <strong>${st.current_co2_ppm || 'N/A'} ppm</strong></div>
                <div style="font-size: 12px; margin-bottom: 2px;">Humidity: <strong>${st.current_humidity_pct || 'N/A'}%</strong></div>
                <div style="font-size: 11px; margin-top: 6px; color: #059669; font-weight: 600;">STATUS: ACTIVE SENSORS (${st.sensor_count})</div>
            </div>
        `;

        circleMarker.bindPopup(popupContent);
        state.mapMarkers.push(circleMarker);
    });
}

function renderStationList(stations) {
    const container = document.getElementById('station-list-container');
    if (!container) return;
    container.innerHTML = '';

    stations.forEach(st => {
        const card = document.createElement('div');
        card.className = 'station-card';
        card.onclick = () => focusStationOnMap(st.lat, st.lon);
        card.innerHTML = `
            <div class="station-card-title">
                <span>${st.name}</span>
                <span class="text-cyan">${st.current_temp_c ? st.current_temp_c + '°C' : ''}</span>
            </div>
            <div class="station-card-meta">
                ID: ${st.station_id} | Elev: ${st.elevation_m}m | Sensors: ${st.sensor_count}
            </div>
        `;
        container.appendChild(card);
    });

    document.getElementById('active-stations-count').textContent = `${stations.length} Active`;
}

function focusStationOnMap(lat, lon) {
    if (state.map) {
        state.map.flyTo([lat, lon], 5, { duration: 1.2 });
    }
}

function filterStationList() {
    const query = document.getElementById('station-search').value.toLowerCase();
    const filtered = state.stations.filter(s => 
        s.name.toLowerCase().includes(query) || 
        s.station_id.toLowerCase().includes(query) ||
        s.zone_id.toLowerCase().includes(query)
    );
    renderStationList(filtered);
}

// =========================================================================
// TAB 3: MapReduce Console
// =========================================================================
function updateMRJobDesc() {
    const sel = document.getElementById('mr-job-select').value;
    const descBox = document.getElementById('mr-job-description');
    if (sel === 'job_temp_anomalies') {
        descBox.innerHTML = '<strong>Job Architecture:</strong> Computes 30-day baseline monthly normals per zone in parallel mappers, then reducers emit deviations &Delta;T.';
    } else if (sel === 'job_ghg_emissions') {
        descBox.innerHTML = '<strong>Job Architecture:</strong> Mappers aggregate annual GHG levels (CO2, CH4, NDVI), reducers compute warming correlations.';
    } else {
        descBox.innerHTML = '<strong>Job Architecture:</strong> Multi-sensor threshold scanning for heatwaves, cyclones, and droughts with composite severity indexing.';
    }
}

async function executeMapReduceJob(e) {
    e.preventDefault();
    if (state.currentRole !== 'admin' && state.currentRole !== 'analyst') {
        alert('Permission Denied: You do not have access to run cluster jobs.');
        return;
    }

    const jobId = document.getElementById('mr-job-select').value;
    const zoneFilter = document.getElementById('mr-zone-filter').value;
    const btn = document.getElementById('btn-run-mr');
    const stagesContainer = document.getElementById('mr-stages');
    const statusPill = document.getElementById('mr-status-pill');

    btn.disabled = true;
    stagesContainer.style.display = 'block';
    statusPill.textContent = 'RUNNING';
    statusPill.className = 'badge badge-warning';

    // Animated Pipeline Stages
    const setStage = (stageId, pct, status) => {
        document.getElementById(`bar-${stageId}`).style.width = `${pct}%`;
        document.getElementById(`stage-${stageId}-status`).textContent = status;
    };

    setStage('input', 30, 'READING BLOCKS (110)');
    await new Promise(r => setTimeout(r, 250));
    setStage('input', 100, 'COMPLETED (40,180 recs)');

    setStage('map', 40, 'MAPPING IN PARALLEL (16 Tasks)');
    await new Promise(r => setTimeout(r, 300));
    setStage('map', 100, 'MAPPERS COMPLETE');

    setStage('shuffle', 60, 'HASH PARTITION & SORT');
    await new Promise(r => setTimeout(r, 250));
    setStage('shuffle', 100, 'SHUFFLE COMPLETE');

    setStage('reduce', 50, 'REDUCING KEYS (4 Nodes)');

    try {
        const res = await authFetch('/api/mapreduce/run', {
            method: 'POST',
            body: JSON.stringify({ job_id: jobId, zone_filter: zoneFilter })
        });
        const report = await res.json();
        if (report.error) {
            throw new Error(report.error);
        }

        setStage('reduce', 100, 'SUCCESS (SAVED TO HDFS)');
        statusPill.textContent = 'SUCCEEDED';
        statusPill.className = 'badge badge-success';
        document.getElementById('mr-throughput').textContent = `${Number(report.throughput_records_per_sec).toLocaleString()} rec/s`;

        document.getElementById('mr-results-json').textContent = JSON.stringify(report, null, 2);
    } catch (err) {
        statusPill.textContent = 'FAILED';
        statusPill.className = 'badge badge-crimson';
        document.getElementById('mr-results-json').textContent = `Error: ${err.message}`;
    } finally {
        btn.disabled = false;
    }
}

// =========================================================================
// TAB 4: AI & Machine Learning Sandbox
// =========================================================================
function updateSlider(name, val) {
    if (name === 'target-year') {
        document.getElementById('val-target-year').textContent = val;
    } else if (name === 'co2-scenario') {
        document.getElementById('val-co2-scenario').textContent = `${val} ppm`;
    }
}

function initForecastChart() {
    const ctx = document.getElementById('forecastChart').getContext('2d');
    state.charts.forecast = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Projected Mean Temp (°C)',
                    data: [],
                    borderColor: '#00f0ff',
                    backgroundColor: 'rgba(0, 240, 255, 0.15)',
                    fill: true,
                    borderWidth: 2,
                    tension: 0.3
                },
                {
                    label: '95% Upper Bound',
                    data: [],
                    borderColor: 'rgba(239, 68, 68, 0.4)',
                    borderDash: [3, 3],
                    borderWidth: 1.5,
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: '95% Lower Bound',
                    data: [],
                    borderColor: 'rgba(16, 185, 129, 0.4)',
                    borderDash: [3, 3],
                    borderWidth: 1.5,
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8', font: { size: 11 } } }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#00f0ff' } }
            }
        }
    });

    runMLForecast();
}

async function runMLForecast() {
    const zoneId = document.getElementById('ml-forecast-zone').value;
    const targetYear = parseInt(document.getElementById('slider-target-year').value);
    const co2Scenario = parseFloat(document.getElementById('slider-co2-scenario').value);

    try {
        const res = await authFetch('/api/predict/forecast', {
            method: 'POST',
            body: JSON.stringify({ zone_id: zoneId, target_year: targetYear, co2_scenario_ppm: co2Scenario })
        });
        const data = await res.json();
        if (data.error) {
            console.error('Forecast error:', data.error);
            return;
        }

        if (state.charts.forecast && data.timeline_years) {
            state.charts.forecast.data.labels = data.timeline_years;
            state.charts.forecast.data.datasets[0].data = data.predicted_mean_temps_c;
            state.charts.forecast.data.datasets[1].data = data.confidence_upper_c;
            state.charts.forecast.data.datasets[2].data = data.confidence_lower_c;
            state.charts.forecast.update();

            const deltaVal = data.net_warming_projected_c >= 0 ? `+${data.net_warming_projected_c} °C` : `${data.net_warming_projected_c} °C`;
            document.getElementById('forecast-delta-val').textContent = deltaVal;
        }
    } catch (err) {
        console.error('Forecast error:', err);
    }
}

async function testAnomalyModel(e) {
    e.preventDefault();
    const payload = {
        surface_temp_c: parseFloat(document.getElementById('test-temp').value),
        precipitation_mm: parseFloat(document.getElementById('test-precip').value),
        humidity_pct: parseFloat(document.getElementById('test-humidity').value),
        pressure_hpa: parseFloat(document.getElementById('test-pressure').value),
        wind_speed_kmh: parseFloat(document.getElementById('test-wind').value),
        co2_ppm: parseFloat(document.getElementById('test-co2').value),
        solar_irradiance_wm2: parseFloat(document.getElementById('test-solar') ? document.getElementById('test-solar').value : 280.0),
        aerosol_optical_depth: parseFloat(document.getElementById('test-aerosol') ? document.getElementById('test-aerosol').value : 0.15)
    };

    try {
        const res = await authFetch('/api/predict/anomaly', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.error) {
            alert('Permission denied: ' + data.error);
            return;
        }

        const score = data.anomaly_score_index;
        const fill = document.getElementById('anomaly-gauge-fill');
        const num = document.getElementById('anomaly-score-num');
        const conf = document.getElementById('anomaly-confidence');
        const tag = document.getElementById('anomaly-classification');

        fill.style.width = `${Math.min(100, Math.max(5, score))}%`;
        num.textContent = `${score} / 100`;
        conf.textContent = `${data.confidence_pct}%`;

        if (data.is_anomaly) {
            tag.className = 'anomaly-tag tag-red';
            tag.textContent = data.classification.replace('_', ' ');
        } else {
            tag.className = 'anomaly-tag tag-green';
            tag.textContent = 'NORMAL BASELINE';
        }
    } catch (err) {
        console.error('Anomaly test error:', err);
    }
}

// =========================================================================
// TAB 5: Real-Time Sensor Stream
// =========================================================================
function initStreamChart() {
    const ctx = document.getElementById('liveStreamChart').getContext('2d');
    state.charts.stream = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Live Temperature (°C)',
                    data: [],
                    borderColor: '#00f0ff',
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 3,
                    pointBackgroundColor: '#00f0ff'
                },
                {
                    label: 'CO2 ppm (scaled / 10)',
                    data: [],
                    borderColor: '#10b981',
                    borderWidth: 1.5,
                    borderDash: [3, 3],
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

function startStreaming() {
    if (state.streamTimer) clearInterval(state.streamTimer);
    state.streamTimer = setInterval(async () => {
        if (!state.streamingActive) return;
        try {
            const res = await fetch('/api/stream/telemetry');
            const packet = await res.json();

            // Update Stream Chart
            if (state.charts.stream) {
                const chart = state.charts.stream;
                const timeLabel = packet.timestamp.split(' ')[1];
                
                chart.data.labels.push(timeLabel);
                chart.data.datasets[0].data.push(packet.surface_temp_c);
                chart.data.datasets[1].data.push(packet.co2_ppm / 10.0);

                if (chart.data.labels.length > 20) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[1].data.shift();
                }
                chart.update('none');
            }

            // Prepend to feed list
            const feedList = document.getElementById('stream-feed-list');
            if (feedList) {
                const row = document.createElement('div');
                row.className = `stream-packet-row ${packet.is_anomaly ? 'anomaly' : ''}`;
                row.innerHTML = `
                    <span>[${packet.timestamp.split(' ')[1]}] <strong>${packet.station_id}</strong> (${packet.station_name})</span>
                    <span>Temp: <strong>${packet.surface_temp_c}°C</strong> | CO2: <strong>${packet.co2_ppm}ppm</strong> | Humidity: ${packet.humidity_pct}%</span>
                    <span class="badge ${packet.is_anomaly ? 'badge-crimson' : 'badge-success'}">${packet.anomaly_reason}</span>
                `;
                feedList.insertBefore(row, feedList.firstChild);

                while (feedList.children.length > 15) {
                    feedList.removeChild(feedList.lastChild);
                }
            }
        } catch (err) {
            console.error('Stream poll error:', err);
        }
    }, 1500);
}

function toggleStreaming() {
    state.streamingActive = !state.streamingActive;
    const btnText = document.getElementById('stream-toggle-text');
    const btnIcon = document.getElementById('stream-toggle-icon');
    const pill = document.getElementById('stream-live-pill');

    if (state.streamingActive) {
        btnText.textContent = 'Pause Stream';
        if (btnIcon) btnIcon.setAttribute('data-lucide', 'pause');
        pill.textContent = 'LIVE (1.5s interval)';
        pill.className = 'badge badge-success';
    } else {
        btnText.textContent = 'Resume Stream';
        if (btnIcon) btnIcon.setAttribute('data-lucide', 'play');
        pill.textContent = 'PAUSED';
        pill.className = 'badge badge-warning';
    }
    lucide.createIcons();
}

// =========================================================================
// TAB 6: Early Warnings & Alerts
// =========================================================================
async function loadAlerts() {
    try {
        const res = await fetch('/api/alerts');
        const alerts = await res.json();
        const container = document.getElementById('alerts-feed-container');
        if (!container) return;

        container.innerHTML = '';
        alerts.forEach(alt => {
            const card = document.createElement('div');
            card.className = `alert-card-item ${alt.severity}`;
            card.innerHTML = `
                <div class="alert-item-header">
                    <span class="alert-item-title">${alt.title}</span>
                    <span class="badge ${alt.severity === 'CRITICAL' ? 'badge-crimson' : (alt.severity === 'HIGH' ? 'badge-warning' : 'badge-info')}">${alt.severity}</span>
                </div>
                <div class="alert-item-body">
                    <div>Zone: <strong>${alt.zone_name} (${alt.zone_id})</strong></div>
                    <div>Triggered Threshold: <span class="font-mono text-crimson">${alt.metric_triggered}</span> (Observed: <strong>${alt.current_value}</strong>)</div>
                    <div style="margin-top: 4px;">Action Protocol: <em>${alt.action_required}</em></div>
                </div>
                <div class="alert-item-footer">
                    <span>ID: ${alt.alert_id}</span>
                    <span>${alt.timestamp}</span>
                </div>
            `;
            container.appendChild(card);
        });

        document.getElementById('alerts-count-badge').textContent = `${alerts.length} Active`;
    } catch (err) {
        console.error('Failed to load alerts:', err);
    }
}

async function loadAlertConfig() {
    try {
        const res = await fetch('/api/alerts/config');
        const cfg = await res.json();
        document.getElementById('cfg-temp-heatwave').value = cfg.temp_heatwave_c || 38.0;
        document.getElementById('cfg-arctic-anom').value = cfg.temp_arctic_anomaly_c || 6.0;
        document.getElementById('cfg-co2-critical').value = cfg.co2_critical_ppm || 440.0;
        document.getElementById('cfg-wind-storm').value = cfg.wind_storm_kmh || 65.0;
        if (document.getElementById('cfg-pm25')) document.getElementById('cfg-pm25').value = cfg.pm25_unhealthy_ugm3 || 55.0;
        if (document.getElementById('cfg-pressure')) document.getElementById('cfg-pressure').value = cfg.pressure_cyclone_drop_hpa || 988.0;
        document.getElementById('cfg-email').checked = !!cfg.email_notifications;
        if (document.getElementById('cfg-sms')) document.getElementById('cfg-sms').checked = !!cfg.sms_broadcast;
    } catch (err) {
        console.error('Failed to load alert config:', err);
    }
}

async function saveAlertConfig(e) {
    e.preventDefault();
    if (state.currentRole !== 'admin' && state.currentRole !== 'analyst') {
        alert('Permission Denied: You do not have access to modify alerting rules.');
        return;
    }

    const payload = {
        temp_heatwave_c: parseFloat(document.getElementById('cfg-temp-heatwave').value),
        temp_arctic_anomaly_c: parseFloat(document.getElementById('cfg-arctic-anom').value),
        co2_critical_ppm: parseFloat(document.getElementById('cfg-co2-critical').value),
        wind_storm_kmh: parseFloat(document.getElementById('cfg-wind-storm').value),
        pm25_unhealthy_ugm3: parseFloat(document.getElementById('cfg-pm25') ? document.getElementById('cfg-pm25').value : 55.0),
        pressure_cyclone_drop_hpa: parseFloat(document.getElementById('cfg-pressure') ? document.getElementById('cfg-pressure').value : 988.0),
        email_notifications: document.getElementById('cfg-email').checked,
        sms_broadcast: document.getElementById('cfg-sms') ? document.getElementById('cfg-sms').checked : false
    };

    try {
        const res = await authFetch('/api/alerts/config', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        const resData = await res.json();
        alert('Alert thresholds updated successfully!');
    } catch (err) {
        alert('Failed to update alert config: ' + err.message);
    }
}

// =========================================================================
// TAB 7: Support & Incident Tickets
// =========================================================================
async function loadTickets() {
    try {
        const res = await fetch('/api/tickets');
        const tickets = await res.json();
        const tbody = document.getElementById('tickets-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        tickets.forEach(tck => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong class="font-mono text-cyan">${tck.ticket_id}</strong></td>
                <td><strong>${tck.title}</strong><div style="font-size: 11px; color: #64748b;">${tck.description.slice(0, 75)}...</div></td>
                <td><span class="badge badge-info">${tck.category}</span></td>
                <td><span class="badge ${tck.priority === 'CRITICAL' || tck.priority === 'HIGH' ? 'badge-crimson' : 'badge-warning'}">${tck.priority}</span></td>
                <td>${tck.author}</td>
                <td><span class="font-mono">${tck.station_id}</span></td>
                <td>${tck.created_at.split(' ')[0]}</td>
                <td><span class="badge ${tck.status === 'RESOLVED' ? 'badge-success' : 'badge-primary'}">${tck.status}</span></td>
                <td>
                    ${tck.status !== 'RESOLVED' && state.currentRole === 'admin' ? 
                        `<button class="btn btn-sm btn-outline" onclick="resolveTicket('${tck.ticket_id}')">Resolve</button>` : 
                        '<span class="text-dim">--</span>'
                    }
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Failed to load tickets:', err);
    }
}

function openNewTicketModal() {
    document.getElementById('ticket-modal').style.display = 'flex';
}

function closeNewTicketModal() {
    document.getElementById('ticket-modal').style.display = 'none';
}

async function submitNewTicket(e) {
    e.preventDefault();
    const payload = {
        title: document.getElementById('tck-title').value,
        category: document.getElementById('tck-category').value,
        priority: document.getElementById('tck-priority').value,
        station_id: document.getElementById('tck-station').value,
        description: document.getElementById('tck-desc').value,
        author: state.currentRole === 'admin' ? 'Chief Operations Lead' : 'Field Climate Analyst'
    };

    try {
        const res = await authFetch('/api/tickets', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        await res.json();
        closeNewTicketModal();
        document.getElementById('new-ticket-form').reset();
        loadTickets();
        alert('Incident ticket logged successfully!');
    } catch (err) {
        alert('Failed to create ticket: ' + err.message);
    }
}

async function resolveTicket(ticketId) {
    try {
        await authFetch('/api/tickets/update', {
            method: 'POST',
            body: JSON.stringify({ ticket_id: ticketId, status: 'RESOLVED' })
        });
        loadTickets();
    } catch (err) {
        console.error('Ticket resolve error:', err);
    }
}

// =========================================================================
// TAB 4 (continued): Climate Impact & Vulnerability Model
// =========================================================================
async function testImpactModel(e) {
    e.preventDefault();
    const payload = {
        co2_ppm: parseFloat(document.getElementById('impact-co2').value),
        ch4_ppb: parseFloat(document.getElementById('impact-ch4').value),
        global_deforestation_rate_mha: parseFloat(document.getElementById('impact-deforest').value),
        fossil_fuel_emissions_gtco2: parseFloat(document.getElementById('impact-fossil').value),
        arctic_sea_ice_extent_mkm2: parseFloat(document.getElementById('impact-ice').value)
    };

    try {
        const res = await authFetch('/api/predict/impact', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.error) {
            alert('Permission denied: ' + data.error);
            return;
        }

        const resultBox = document.getElementById('impact-result-box');
        resultBox.style.display = 'block';

        const riskScore = data.climate_vulnerability_index;
        document.getElementById('impact-risk-score').textContent = `${riskScore} / 100`;
        document.getElementById('impact-event-mult').textContent = `${data.extreme_event_multiplier}x`;
        document.getElementById('impact-sea-level').textContent = `${data.sea_level_rise_trajectory_cm_decade} cm/decade`;

        const gaugeFill = document.getElementById('impact-gauge-fill');
        gaugeFill.style.width = `${Math.min(100, Math.max(5, riskScore))}%`;

        const tierTag = document.getElementById('impact-tier-tag');
        tierTag.textContent = data.vulnerability_tier.replace(/_/g, ' ');
        if (riskScore > 75) {
            tierTag.className = 'anomaly-tag tag-red';
        } else if (riskScore > 50) {
            tierTag.className = 'anomaly-tag tag-red';
        } else if (riskScore > 25) {
            tierTag.className = 'anomaly-tag tag-green';
        } else {
            tierTag.className = 'anomaly-tag tag-green';
        }
    } catch (err) {
        console.error('Impact model error:', err);
    }
}
