# DocGuard AI — Identity & Document Screening System

An AI-powered border-control platform that screens identity documents (passports,
visas, national IDs, driving licenses), extracts data via OCR, validates against
ICAO/MRZ rules, detects tampering, verifies faces, and outputs a risk score.

---

## Tech Stack & Requirements

| Layer | Technology | Requirement |
|-------|-----------|-------------|
| Frontend | Next.js 14 + TypeScript + Tailwind + shadcn/ui | **Node.js ≥ 18** + npm |
| Backend | FastAPI + Python | **Python 3.9–3.12** (64-bit) |
| OCR | RapidOCR (ONNX PaddleOCR port) + MRZ parser + ICAO 9303 checksum | `rapidocr-onnxruntime` |
| Tampering | OpenCV + Error Level Analysis (ELA) | `opencv-python` |
| Face | InsightFace (ArcFace) + OpenCV fallback | `insightface`, `onnxruntime` |
| Database | PostgreSQL + SQLAlchemy (SQLite in dev) | `psycopg2-binary` (SQLite works with zero config) |
| Deployment | Docker / docker-compose | Docker Desktop (optional) |

### Minimum Requirements
- **Python 3.9+** — backend (tested on 3.12/3.13)
- **Node.js ≥ 18 + npm** — frontend (tested on Node 20 LTS)
- ~2–4 GB free disk (ML model/package downloads)

> **Note:** RapidOCR requires no external binaries (ONNX Runtime). The optional
> `pytesseract` fallback additionally needs the [Tesseract OCR binary](https://github.com/UB-Mannheim/tesseract/wiki)
> installed and in PATH — but it is NOT required; RapidOCR does the work.

---

## Project Structure

```
Default Project/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py          # App entry point (serves API + built-in UI)
│   │   ├── config.py        # Settings (DB URL, weights, etc.)
│   │   ├── database.py      # SQLAlchemy models + session
│   │   ├── api/screening.py # REST endpoints
│   │   ├── modules/
│   │   │   ├── document_ocr.py      # Module 1: OCR + MRZ
│   │   │   ├── mrz_parser.py        # ICAO 9303 MRZ + checksum
│   │   │   ├── document_validator.py# Module 2: validation
│   │   │   ├── tampering_detector.py# Module 3: ELA + OpenCV
│   │   │   └── face_verifier.py     # Module 4: InsightFace
│   │   └── services/risk_scorer.py  # weighted risk engine
│   ├── static/              # Built-in web UI
│   ├── uploads/             # processed document images
│   ├── requirements.txt
│   ├── start.bat            # one-click backend launcher (Windows)
│   └── Dockerfile
├── frontend/                # Next.js app
│   ├── app/                 # routes (dashboard, screening, history)
│   ├── components/          # shadcn/ui + feature components
│   ├── services/api.ts      # REST client
│   ├── package.json
│   ├── .env.example
│   └── Dockerfile
├── docker-compose.yml       # Postgres + backend + frontend
└── RUN_GUIDE.md
```

---

## Option A — Run backend with built-in web UI (simplest, no Node)

The backend serves a complete web interface by itself, so you can use the app
without installing Node.js at all.

### 1. Install Python dependencies
```bash
cd backend

# Create & activate a virtual environment (recommended on all machines)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Start the backend
```bash
python -m uvicorn app.main:app --reload
```

**Windows one-click alternative:** double-click `start.bat`. The script is
portable — it automatically uses a local `venv` if present, or falls back to
whatever `python` is on PATH, and offers to install the dependencies if they
are missing. So it works on any teammate's machine without editing anything.

### 3. Use it
Open **http://localhost:8000** in your browser.

---

## Option B — Run full stack (backend + Next.js frontend)

This gives you the richer Next.js/TypeScript UI on port 3000.

### 1. Start the backend (from Option A, step 1–2)
Keep this terminal running in the `backend` folder.

### 2. Install & start the frontend (separate terminal)
```bash
cd frontend
npm install
# configure the API base URL it proxies to (default http://localhost:8000)
cp .env.example .env.local
npm run dev
```

### 3. Use it
Open **http://localhost:3000**.

> Both servers must run together. The frontend proxies `/api/*` to the backend
> (set in `next.config.js` / `.env.local` via `API_BASE_URL`).

---

## Option C — Docker (PostgreSQL + backend + frontend)

If you have Docker Desktop, one command runs everything:

```bash
cd "Default Project"
docker-compose up --build
```

- Frontend: **http://localhost:3000**
- Backend: **http://localhost:8000**
- PostgreSQL on port 5432 (user/pass/db = `docguard`)

---

## Using the App

1. Open the Dashboard — shows totals, flagged, high-risk, and charts.
2. Go to **New Screening** → pick a document type → upload an image → **Start Screening**.
3. Review the result:
   - **Extracted data** (name, numbers, nationality, DOB, expiry, gender)
   - **Validation** (incl. MRZ ICAO 9303 checksum — detects forged number/date/expiry)
   - **Tampering** score (ELA + copy-move + stamp + metadata)
   - **Face match** (document vs live photo, if provided)
   - **Risk score** 0–100 and level (Low / Medium / High / Critical)
4. Browse **Screening History** and open detailed results.

### API Reference
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/screening/documents?document_type=passport` | Upload + screen a document (multipart `file`) |
| GET | `/api/screening/results` | All screening records |
| GET | `/api/screening/{id}` | One screening record |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| POST | `/api/screening/{id}/decision` | Approve/reject a document |
| GET | `/health` | Health check |

---

## Configuration

Settings live in `backend/app/config.py` and can be overridden via environment
variables or a `.env` file in `backend/`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./screening.db` | Set to `postgresql://user:pass@host/db` for Postgres |
| `TAMPERING_WEIGHT` | `0.4` | Risk weight for tampering |
| `VALIDATION_WEIGHT` | `0.3` | Risk weight for validation |
| `FACE_MATCH_WEIGHT` | `0.3` | Risk weight for face match |
| `UPLOAD_DIR` | `uploads` | Where document images are stored |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `python: No module named uvicorn` | You may have multiple Pythons. Activate the venv (`venv\Scripts\activate`) or use the interpreter that has the packages. On Windows, `start.bat` auto-selects the right interpreter. |
| `ModuleNotFoundError: ...` | Run `pip install -r requirements.txt` inside the backend venv. |
| Port already in use | Backend: use `--port 8001`. Update frontend `API_BASE_URL`/`next.config.js` to match. |
| Frontend shows no styles | Be sure the URL paths are correct. Built-in UI loads `/static/styles.css`. |
| Frontend can't reach backend | Backend must be running (Option A step 2). Check `API_BASE_URL` in `.env.local`. |
| Slow first OCR run | RapidOCR downloads ONNX models on first use; subsequent runs are fast. |
| `tesseract is not installed` | Ignore — that's only the optional fallback. RapidOCR handles OCR. |

---

## License / Notes
Built as a prototype for AI-based identity document screening. For production,
add TLS, a real operator-auth layer, and strict data retention controls.
