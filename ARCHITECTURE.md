# Data Detective — Valencia Urban Intel

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                       DATA DETECTIVE                                    │
│                              Valencia Urban Intelligence Platform                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                         MAIN                                            │
│  1. Splash Screen → data_verifier.py (checks historical data integrity)                 │
│  2. Pre-load 3 real-time APIs in parallel threads (5-min TTL cache)                     │
│  3. Mount 3-panel UI (Flet desktop app)                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                          │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
        ┌───────────────────┐   ┌─────────────────────┐   ┌───────────────────────┐
        │    LEFT PANEL     │   │    MAP CONTAINER    │   │     RIGHT PANEL       │
        │   (280px wide)    │   │   (center, flex)    │   │  (500-800px, resiz.)  │
        ├───────────────────┤   ├─────────────────────┤   ├───────────────────────┤
        │ Layer Selector    │   │ Interactive Map     │   │ Month/Year Picker     │
        │  · Precipitation  │   │ flet-map component  │   │ Historical Layers:    │
        │  · NO2            │   │                     │   │  · Pollution          │
        │  · O3 / PM10      │   │ Tile Styles:        │   │  · Rain (AEMET)       │
        │  · Traffic        │   │  · CartoDB Light    │   │  · Traffic            │
        │                   │   │  · ESRI Satellite   │   │                       │
        │ LIVE Indicator    │   │  · CartoDB Dark     │   │ Mini-Map              │
        │                   │   │  · OpenTopoMap      │   │ (sensor locations)    │
        │ Top 6 Node Cards  │   │                     │   │                       │
        │ (by severity)     │   │ Clickable Markers   │   │ Interactive Charts    │
        │  · NO2 levels     │   │ (color-coded)       │   │ (Flet native)         │
        │  · Precipitation  │   │ Polylines (traffic) │   │                       │
        │  · Traffic jams   │   │ Info Card on click  │   │ Export:               │
        │                   │   │                     │   │  · JSON               │
        │                   │   │                     │   │  · CSV                │
        │                   │   │                     │   │  · PDF Report         │
        └───────────────────┘   └─────────────────────┘   └───────────────────────┘
```

---

## 🔄 Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL DATA SOURCES                           │
├──────────────────────┬──────────────────────┬────────────────────────────┤
│  GVA CKAN API        │  AEMET OpenData API  │  Valencia Geoportal        │
│  (dadesobertes)      │  (climate data)      │  (ArcGIS REST)             │
│  Pollution CSVs      │                      │  Air + Traffic             │
├──────────────────────┴──────────────────────┴────────────────────────────┤
│                          AVAMET (web scraping)                           │
│                          https://www.avamet.org                          │
└──────────────────────────────────────────────────────────────────────────┘
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ GetContaminacio │     │ AEMETDownloader     │     │ RealTimeAirValencia │
│ .py             │     │ .py + AEMETData     │     │ RealTimeTraffic     │
│                 │     │ Service.py          │     │ ValencianWeather.py │
└────────┬────────┘     └──────────┬──────────┘     └──────────┬──────────┘
         │                         │                           │
         ▼                         ▼                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          LOCAL DATA STORAGE                              │
├──────────────────────┬──────────────────────┬────────────────────────────┤
│ data/pollution_      │ data/aemet_          │ data/trafico_valencia.     │
│ historical/          │ historical/          │ parquet                    │
│ YYYY.json            │ monthly_*.json       │                            │
│ (1994-2025)          │ (2007-2024)          │ (2016-2026)                │
│ metadata.json        │                      │                            │
└──────────────────────┴──────────────────────┴────────────────────────────┘
         │                         │                           │
         ▼                         ▼                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        DATA LOADING & CACHING                            │
├──────────────────────────────────────────────────────────────────────────┤
│  async_data_loader.py          │  data_service.py                        │
│  · Thread-safe JSON loading    │  · DataCache (5-min TTL)               │
│  · Parquet reading (pandas)    │  · get_cached_weather_data()           │
│  · Historical stats calc       │  · get_cached_air_quality_data()       │
│                                │  · get_cached_traffic_data()           │
└──────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                            UI RENDERING                                  │
├──────────────┬──────────────────┬────────────────────────────────────────┤
│ LeftPanel    │ MapContainer     │ RightPanel                             │
│ · Node cards │ · Markers        │ · Historical browsing (month/year)     │
│ · Severity   │ · Polylines      │ · Mini-map                             │
│ · Live data  │ · Tile layers    │ · Charts + Export                      │
└──────────────┴──────────────────┴────────────────────────────────────────┘
```

---

## 🧩 Component Detail

### LeftPanel (`components/left_panel.py`)
```
┌─────────────────────────────┐
│  INTELLIGENCE LAYERS        │
│  ○ Precipitation            │
│  ○ NO2                      │
│  ○ O3 / PM10                │
│  ○ Traffic                  │
├─────────────────────────────┤
│  ● LIVE  (auto-refresh)     │
├─────────────────────────────┤
│  MOST RELEVANT NODES        │
│  ┌───────────────────────┐  │
│  │ 🟢 Station X          │  │
│  │ NO2: 45 µg/m³         │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │ 🟡 Station Y          │  │
│  │ PM10: 62 µg/m³        │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │ 🔴 Road Z (cong.)     │  │
│  │ Speed: 12 km/h        │  │
│  └───────────────────────┘  │
│         ... (up to 6)       │
└─────────────────────────────┘
```

### MapContainer (`components/map_container.py`)
```
┌─────────────────────────────────────────┐
│  [☰ Tile Style ▼]  [Layers ▼]          │
├─────────────────────────────────────────┤
│                                         │
│         🟢  ·  (precipitation marker)   │
│    ·         🔵  (NO2 marker)           │
│              ·     🟣 (O3 marker)       │
│     🟢          ════ (traffic polyline) │
│         🔵  ·                           │
│              🟣                         │
│    ·  🔴 (alert marker)                │
│                                         │
├─────────────────────────────────────────┤
│  📍 Station X — Info Card               │
│  NO2: 45 µg/m³ | PM10: 62 µg/m³        │
│  Rating: Good                            │
└─────────────────────────────────────────┘
```

### RightPanel (`components/right_panel.py`)
```
┌──────────────────────────────────────┐
│  [◀]  April 2025  [▶]               │
├──────────────────────────────────────┤
│  [Pollution] [Rain] [Traffic]        │
├──────────────────────────────────────┤
│                                      │
│  Historical Data Display             │
│  ┌────────────────────────────────┐  │
│  │ Station  | NO2  | O3   | PM10 │  │
│  │ -------- | ---- | ---- | ---- │  │
│  │ St. A    │ 38   │ 52   │ 28   │  │
│  │ St. B    │ 45   │ 61   │ 35   │  │
│  └────────────────────────────────┘  │
│                                      │
│  ─── Mini-Map ───                    │
│  ┌────────────────────┐              │
│  │  🟢  🔵  🟣        │              │
│  │    🔵    🟢         │              │
│  │  🟣     🔵   🟢     │              │
│  └────────────────────┘              │
│                                      │
│  ─── Charts ───                      │
│  (interactive Flet charts)           │
│                                      │
├──────────────────────────────────────┤
│  [Export JSON] [Export CSV]          │
│  [Export PDF Report]                 │
└──────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
Data-Detective/
├── main.py                          # Entry point, splash, UI assembly
├── components/
│   ├── __init__.py
│   ├── left_panel.py                # Layer selector + live node cards
│   ├── map_container.py             # flet-map with markers & polylines
│   ├── right_panel.py               # Historical analysis, charts, export
│   └── ui_elements.py               # Reusable UI factory (cards, badges)
├── config/
│   ├── theme.py                     # Color palette (neon green, dark BG)
│   └── map_styles.py                # Tile layer URL templates
├── utils/
│   ├── data_service.py              # Centralized caching layer (5-min TTL)
│   ├── data_verifier.py             # Startup integrity check + progress UI
│   ├── async_data_loader.py         # Thread-based async data loading
│   ├── historical_data_processor.py # Stats: daily avg, comparisons
│   │
│   │── Real-Time APIs
│   ├── RealTimeAirValencia.py       # ArcGIS REST → Air quality
│   ├── RealTimeTrafficValencia.py   # ArcGIS REST → Traffic
│   ├── RealTimeValencianWeather.py  # AVAMET scraping → Weather
│   │
│   │── Historical Data Pipelines
│   ├── GetContaminacio.py           # GVA CKAN API → pollution CSVs
│   ├── optimized_data_downloader.py # Multi-thread CSV → JSON converter
│   ├── generate_json_indexed.py     # CSV → year-indexed JSON
│   ├── AEMETDataService.py          # AEMET OpenData client
│   ├── AEMET_downloader.py          # AEMET monthly data downloader
│   │
│   │── Coordinate Mappings
│   ├── avamet_coordinates.py        # AVAMET station → GPS lookup
│   └── valencia_stations.json       # AEMET station inventory
├── data/
│   ├── pollution_historical/        # YYYY.json (1994-2025) + metadata.json
│   ├── aemet_historical/            # monthly_*.json (2007-2024)
│   ├── trafico_valencia.parquet     # Traffic historical data
│   └── ods/                         # Source ODS files from GVA
├── assets/                          # App icons, images
└── requirements.txt                 # Python dependencies
```

---

## 🚀 Usage Flow

```
1. START
   └─► python3 main.py
        │
        ├─► [Splash Screen] Verify/download historical data if missing
        │     (first run may take several minutes)
        │
        └─► Pre-load real-time APIs (3 parallel threads, 5-min cache)

2. MAIN UI APPEARS
   │
   ├─► LEFT PANEL: Select an intelligence layer
   │    └─► Top 6 most relevant sensors appear as cards
   │
   ├─► MAP: Click markers to see real-time readings
   │    └─► Change tile style for different map views
   │
   └─► RIGHT PANEL: Browse historical data
        ├─► Navigate months/years with ◀ ▶ buttons
        ├─► Switch between Pollution / Rain / Traffic
        ├─► View mini-map of sensor locations
        ├─► Analyze interactive charts
        └─► Export data (JSON / CSV / PDF)

3. REAL-TIME REFRESH
   └─► Data auto-refreshes every 5 minutes (cache TTL)
   └─► LIVE indicator shows active status
```

---

## 📊 Data Sources & Coverage

| Source | Type | Time Range | Update Frequency |
|--------|------|------------|-----------------|
| **GVA CKAN** | Air Pollution (NO2, O3, PM10) | 1994–2025 | Historical (annual updates) |
| **AEMET OpenData** | Weather (temp, humidity, rain, wind) | 2007–2024 | Historical (monthly updates) |
| **Valencia Geoportal (ArcGIS)** | Real-time Air Quality | Current | Real-time (5-min cache) |
| **Valencia Geoportal (ArcGIS)** | Real-time Traffic (intensity, speed, occupancy) | 2016–2026 | Real-time (5-min cache) |
| **AVAMET** (scraped) | Real-time Weather | Current | Real-time (5-min cache) |

---

## 🎨 Color Legend

| Color | Hex | Layer |
|-------|-----|-------|
| 🟢 Neon Green | `#00ff88` | Precipitation / Primary UI |
| 🔵 Blue | `#4a9eff` | NO2 |
| 🟣 Purple | `#9b4aff` | O3 / PM10 (Pollution) |
| 🟠 Orange | `#ffaa00` | Traffic |
| 🔴 Red | `#ff4444` | Danger / Alerts |
| ⚫ Dark BG | `#0a0e1a` | Application background |
