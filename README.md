# UrbanCool AI

AI/ML decision-support platform for urban heat mitigation. It detects urban
heat hotspots, explains their causes, predicts heat risk, simulates cooling
interventions, recommends and **optimizes** cooling strategies, advises on
**cost**, shows **air quality**, and generates reports — using real satellite
data from Google Earth Engine.

Workflow: **Detect → Explain → Predict → Simulate → Recommend → Optimize → Report**

---

## Features

- **Heat hotspot detection** — 30 real zones per city, mapped at real locations.
- **Driver analysis** — why a zone is hot (vegetation, built-up, surface temp, water, weather).
- **Heat risk prediction** — RandomForest model with a rule-based fallback.
- **Cooling simulator** — estimate temperature reduction from interventions.
- **Cooling optimizer** — pick the highest-impact zones and best intervention mix city-wide.
- **Cost advisor** — minimum-cost plan to hit a temperature target + savings vs an unplanned mix.
- **Air Quality Index** — real-time CPCB AQI from data.gov.in (with fallback).
- **Reports** — JSON report + downloadable PDF per zone.
- **Demo-safe** — every external dependency falls back to local data; the app never crashes.

## Tech Stack

- **Backend:** Python, FastAPI, scikit-learn, pandas, numpy, joblib, fpdf2, earthengine-api.
- **Frontend:** React, Vite, Tailwind CSS, React Router, Leaflet + React Leaflet, Recharts, Axios, Lucide.
- **Data:** Google Earth Engine (Sentinel-2 NDVI, Landsat 8/9 LST), data.gov.in AQI, Open-Meteo weather, OpenStreetMap names.

## Project Structure

```
ISRO/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app, CORS, routers
│   │   ├── config.py              # env settings
│   │   ├── models/                # schemas + ML model wrapper
│   │   ├── routes/                # API endpoints
│   │   ├── services/              # data, prediction, recommendation,
│   │   │                          # simulation, priority, optimize, cost,
│   │   │                          # air quality, report, GEE
│   │   └── data/                  # hotspot + city JSON
│   ├── ml/
│   │   ├── train_model.py         # train RandomForest
│   │   ├── evaluate_model.py      # sanity-check predictions
│   │   ├── fetch_gee_data.py      # refresh indices for existing zones
│   │   └── generate_zones.py      # build 30 real zones per city from GEE
│   ├── secrets/                   # GEE key (git-ignored)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
└── frontend/
    ├── src/
    │   ├── pages/                 # Landing, Dashboard, Simulator,
    │   │                          # Optimize, CostAdvisor, Reports
    │   ├── components/            # Map, cards, charts, navbar, etc.
    │   ├── api/api.js             # backend client
    │   ├── data/demoData.js       # offline fallback
    │   └── utils/                 # constants + helpers
    ├── package.json
    └── .env.example
```

---

## Setup & Run

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env       # Windows  (cp on macOS/Linux)
python ml/train_model.py     # optional; rule-based fallback works without it
python run.py
```

Backend: `http://localhost:8000` · Swagger docs: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

The frontend reads the backend URL from `VITE_API_BASE_URL` (default
`http://localhost:8000`). It works on demo data even if the backend is offline.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Project info |
| GET | `/api/health` | Backend health |
| GET | `/api/data/status` | Data source status |
| GET | `/api/cities` | Supported cities |
| GET | `/api/hotspots?city=ahmedabad` | Hotspot zones for a city |
| GET | `/api/hotspots/{zone_id}` | Single zone detail |
| POST | `/api/predict` | Heat risk prediction |
| POST | `/api/simulate` | Cooling simulation |
| GET | `/api/optimize?city=&budget=` | City-wide cooling plan |
| GET | `/api/cost-advisor?zone_id=&target=` | Minimum-cost cooling plan |
| GET | `/api/air-quality?city=` | Real-time AQI |
| GET | `/api/report/{zone_id}` | JSON report |
| GET | `/api/report/{zone_id}/download` | PDF report |

---

## Heat Risk Score

Range 0–100 → Low (0–30), Moderate (31–60), High (61–80), Severe (81–100).
Weighted formula: LST 30%, Vegetation 20%, Built-up 20%, Water 10%, Weather 15%,
Wind 5%. The ML model predicts the score; a rule-based fallback guarantees the
API always responds.

## Google Earth Engine (real satellite data)

The platform uses GEE for NDVI (Sentinel-2) and LST (Landsat 8/9).

1. Create a Google Cloud project and enable the Earth Engine API.
2. Register the project for Earth Engine (non-commercial, Community tier).
3. Authenticate locally:
   ```bash
   python -c "import ee; ee.Authenticate()"
   ```
4. In `backend/.env` set:
   ```
   USE_GEE=true
   GEE_PROJECT=your-cloud-project-id
   ```
   (For a server, use a service account key at `backend/secrets/gee-key.json`
   and set `GEE_SERVICE_ACCOUNT` + `GEE_KEY_FILE`.)
5. Generate real zones:
   ```bash
   python ml/generate_zones.py --city ahmedabad --rows 6 --cols 5
   python ml/generate_zones.py --city surat --rows 6 --cols 5
   ```

## Fallback Strategy

Every external dependency degrades gracefully:

- **Hotspots:** live API → cached → local demo JSON.
- **ML model:** trained model → rule-based scoring.
- **Air quality:** data.gov.in → demo AQI.
- **Weather:** Open-Meteo → cached/demo.
- **PDF/report:** backend → frontend demo preview.

This keeps the demo working with or without internet, GEE, or the backend.

## Environment Variables (`backend/.env`)

```
APP_NAME=UrbanCool AI
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
USE_LIVE_API=false
USE_GEE=true
GEE_PROJECT=your-cloud-project-id
DATA_GOV_API_KEY=your-data-gov-in-key
```
