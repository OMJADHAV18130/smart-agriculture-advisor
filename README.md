# 🌾 Smart Agriculture Advisory Expert System

A small **rule-based expert system** built as a college AI Lab mini-project.
A farmer/student enters field observations (crop, soil moisture, rainfall,
temperature, symptoms); the backend runs a **forward-chaining** inference
engine over a knowledge base of IF–THEN agricultural rules, and can also
**backward-chain** to verify a selected goal. A clean React dashboard shows
possible issues, recommendations, triggered rule IDs, inferred facts, and a
readable reasoning trace.

> **This is a rule-based (symbolic AI) system — not an ML model, not a
> chatbot, and no responses are hardcoded in the frontend.** All reasoning
> happens in the Python backend (`backend/app/engine.py`).

## Project structure

```
smart-agriculture-advisor/
├── .env.example               # Full-stack / Docker Compose environment template
├── docker-compose.yml         # Containerized multi-service orchestration
├── frontend/                  # React + Vite + plain CSS
│   ├── .env.example           # Frontend environment template (VITE_API_URL)
│   ├── Dockerfile             # Multi-stage build + Nginx static server
│   ├── nginx.conf             # Nginx reverse proxy / static asset config
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx            # Dashboard: form + results panel
│       ├── App.css            # Green-and-white theme
│       ├── index.css          # Global styles / CSS variables
│       ├── api.js             # Fetch helpers with configurable API URL
│       └── main.jsx           # React entry point
├── backend/                   # Python FastAPI
│   ├── .env.example           # Backend environment template
│   ├── Dockerfile             # Container definition with dynamic PORT/HOST
│   ├── requirements.txt       # Dependencies (FastAPI, uvicorn, python-dotenv, etc.)
│   ├── app/
│   │   ├── main.py            # API routes (/health, /goals, /analyze) + dynamic CORS
│   │   ├── config.py          # Centralized environment configuration
│   │   ├── engine.py          # Forward & backward chaining inference engine
│   │   ├── knowledge_base.py  # IF-THEN rules, thresholds, labels
│   │   ├── schemas.py         # Pydantic request/response models
│   │   └── dataset.py         # Crop dataset loader & statistics
│   ├── data/                  # Cleaned crop recommendation dataset CSV
│   └── tests/
│       ├── test_config.py     # Configuration & origins parsing tests
│       ├── test_dataset.py    # Dataset tests
│       └── test_engine.py     # Inference engine tests
├── .gitignore
└── README.md
```


## Requirements

- Python 3.10+
- Node.js 18+ (with npm)

---

## Setup — Backend (FastAPI)

```bash
cd backend
python -m venv venv
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**macOS / Linux:**
```bash
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Backend URL: **http://localhost:8000**
- Interactive API docs: **http://localhost:8000/docs**
- Health check: **http://localhost:8000/health**

## Setup — Frontend (React + Vite)

Open a **second terminal** (leave the backend running):

```bash
cd frontend
npm install
npm run dev
```

- Frontend URL: **http://localhost:5173**

> CORS is already configured in `backend/app/main.py` to allow
> `http://localhost:5173`.

---

## How to test the system

1. Open **http://localhost:5173** in your browser.
2. Choose observations, e.g.:
   - Crop: `Tomato`
   - Soil moisture: `20%`
   - Rainfall: `No`
   - Temperature: `35`
   - Symptom: `Wilting`
   - Goal: `Irrigation is needed`
3. Press **Analyze**. You should see:
   - A verdict banner (e.g. *Attention likely needed*)
   - **Possible issues**, each tagged with its source rules
   - **Recommendations**
   - **Triggered rules** (e.g. `R01 → R05 → R06 → R12 → R14`)
   - **Inferred facts** produced by chaining
   - **Backward chaining goal check** with a step-by-step proof
   - A collapsible **reasoning trace** (all engine cycles)

### What happens internally

1. Numeric inputs are normalized into symbolic facts
   (`soil_moisture=low`, `temperature=high`, …).
2. **Forward chaining:** rules whose IF-parts match working memory fire,
   their THEN-parts are added as new facts, and the loop repeats **until no
   new facts appear** (fixpoint).
3. **Backward chaining:** the selected goal is proved *backwards* from the
   original user facts — the proof shows which rules were traversed
   (e.g. R03 → R04 for a multi-hop goal).
4. The API returns JSON that the dashboard renders (summary, conclusions,
   recommendations, rule IDs, inferred facts, traces).

### Sample scenarios

| Crop | Moisture | Rain | Temp | Symptom | Expected |
|---|---|---|---|---|---|
| Wheat | 20% | No | 28 | None | `normal`/`monitor` → R01, R14 fire; irrigation advised |
| Tomato | 20% | No | 35 | Wilting | `attention` → heat + water stress + wilting rules |
| Rice | 85% | Yes | 30 | None | Waterlogging possible, irrigation **not** needed |
| Cotton | 75% | Yes | 30 | Leaf Spots | `monitor` → possible fungal issue in wet weather |
| Wheat | 50% | Unknown | 25 | None | `normal` → no issue rules trigger |

### Testing with curl / PowerShell

```powershell
$body = @{
  crop = 'rice'; soil_moisture = 20; rainfall = 'No'
  temperature = 35; humidity = 85; ph = 6.5; symptom = 'Wilting'
  goal = 'irrigation=needed'
} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/analyze -Method Post `
  -ContentType 'application/json' -Body $body
```

### Running the engine tests (forward + backward chaining)

```bash
cd backend
pytest
```

Expected: **9 tests passed** — covering forward chaining (rule firing,
fixpoint termination, blocked rules, transitive chaining, negated
conditions) and backward chaining (supported, refuted, multi-hop goals).

---

## API reference

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Status, rule count, **configurable thresholds** |
| `GET` | `/goals` | Goal options for backward chaining |
| `POST` | `/analyze` | Run forward (+ optional backward) chaining |

`POST /analyze` body:

```json
{
  "crop": "rice",
  "soil_moisture": 20,
  "rainfall": "No",
  "temperature": 35,
  "humidity": 85,
  "ph": 6.5,
  "symptom": "Wilting",
  "goal": "irrigation=needed"
}
```

Response includes: `summary`, `conclusions` (with `category` and
`source_rules`), `recommendations`, `fired_rule_ids`, `inferred_facts`,
`rules_evaluated`, `reasoning_trace`, `backward_chain` (with `proof`),
and a disclaimer `note`.

## The rule knowledge base

16 clearly documented IF–THEN rules in `backend/app/knowledge_base.py`
across five areas:

- **Irrigation** — R01–R02 (when to water / check first), R03 (not needed)
- **Soil / nutrient checks** — R04, R14–R16 (drainage, moisture
  monitoring, rice preference, soil test suggestion)
- **Heat / water stress** — R05, R06, R12, R13
- **Leaf symptoms** — R07–R10
- **Pest monitoring** — R11 (scout/identify before acting)

**Configurable thresholds** live at the top of `knowledge_base.py`
(`THRESHOLDS` dict) and are reported by `/health`. They are labeled
**illustrative demo values**, not agronomic standards.

## Environment Variables & Configuration

The application is fully configurable via environment variables or `.env` files. Templates are provided for each tier.

### Backend Environment Variables (`backend/.env` or root `.env`)

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Runtime environment (`development`, `staging`, `production`) |
| `HOST` | `0.0.0.0` | IP address to bind FastAPI server |
| `PORT` | `8000` | Port to listen on (automatically used by Docker and cloud PaaS like Render/Cloud Run) |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated list of allowed CORS origins, or `*` to allow all origins |
| `LOG_LEVEL` | `info` | Uvicorn logging verbosity (`debug`, `info`, `warning`, `error`) |
| `DATASET_PATH` | `data/cleaned_crop_recommendation.csv` | *(Optional)* Override path to the crop reference CSV |

### Frontend Environment Variables (`frontend/.env` or build environment)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Base URL of the FastAPI backend (e.g. `https://api.yourdomain.com`) |

---

## Deployment Guide

### Option 1: Docker Compose (One-Command Full Stack)

Run both the frontend and backend in production-ready containers:

```bash
# 1. (Optional) Customize environment values
cp .env.example .env

# 2. Build and launch
docker compose up --build
```

- Frontend: **http://localhost:5173** (or your configured `FRONTEND_PORT`)
- Backend: **http://localhost:8000** (or your configured `BACKEND_PORT`)

To stop the containers:
```bash
docker compose down
```

### Option 2: Cloud PaaS Deployment (Render / Railway / Fly.io / GCP Cloud Run)

#### Backend Deployment:
1. Deploy `backend/` using Docker or Python runtime.
2. Set environment variables in the service dashboard:
   - `ENVIRONMENT=production`
   - `ALLOWED_ORIGINS=https://your-frontend-domain.com`
   - `PORT=8000` (or leave default if the platform assigns dynamic `$PORT`)
3. Health check path: `/health`

#### Frontend Deployment (Vercel / Netlify / Cloudflare Pages):
1. Connect the repository and set root directory to `frontend/`.
2. Build command: `npm run build`
3. Output directory: `dist`
4. Set build environment variable:
   - `VITE_API_URL=https://your-backend-service.up.railway.app` (your actual backend URL)

---

## Conservative-advice policy

- Symptoms always suggest **possible** causes, never confirmed diagnoses.
- **No pesticide or fertilizer quantities** are ever recommended.
- Every response carries a disclaimer asking users to consult a local
  agronomy expert.

## Architectural Scope & Simplicity

A lightweight, transparent symbolic AI system without database, authentication, external third-party APIs, or heavy ML models — built purely with FastAPI, Pydantic, and React/Vite for inspectable rule-based inference.

