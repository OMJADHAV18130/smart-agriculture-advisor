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
├── frontend/                  # React + Vite + plain CSS
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx            # Dashboard: form + results panel
│       ├── App.css            # Green-and-white theme
│       ├── index.css          # Global styles / CSS variables
│       ├── api.js             # Fetch helpers for the backend API
│       └── main.jsx           # React entry point
├── backend/                   # Python FastAPI
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py            # API routes (/health, /goals, /analyze) + CORS
│   │   ├── engine.py          # Forward & backward chaining inference engine
│   │   ├── knowledge_base.py  # IF-THEN rules, thresholds, labels
│   │   └── schemas.py         # Pydantic request/response models
│   └── tests/
│       └── test_engine.py     # Sample forward & backward chaining tests
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

## Conservative-advice policy

- Symptoms always suggest **possible** causes, never confirmed diagnoses.
- **No pesticide or fertilizer quantities** are ever recommended.
- Every response carries a disclaimer asking users to consult a local
  agronomy expert.

## Deliberately out of scope (simplicity)

No database, authentication, Docker, external APIs, LLMs, sensors, or
machine learning — only FastAPI, Pydantic, and React/Vite.
