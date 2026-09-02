# AI-Based Fake Identity & Document Screening System

An AI-powered border control document screening platform that automatically analyzes identity documents, detects tampering and forgery, validates against rules, and generates risk scores.

## Tech Stack

```
FRONTEND          Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
BACKEND           FastAPI + Python REST API
DOCUMENT AI       RapidOCR (ONNX PaddleOCR port) + Python MRZ Parser + ICAO 9303 Checksum
TAMPERING         OpenCV + Error Level Analysis (ELA)
FACE              InsightFace (ArcFace) with OpenCV fallback
RISK              Python weighted risk engine
DATABASE          PostgreSQL + SQLAlchemy (SQLite fallback for dev)
STORAGE           Local storage
DEPLOYMENT        Docker / docker-compose (optional)
```

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                Frontend (Next.js + shadcn/ui)            │
│   Dashboard | Screening | History                        │
└──────────────────────────┬───────────────────────────────┘
                           │ REST API (rewrites /api/*)
┌──────────────────────────┴───────────────────────────────┐
│                Backend (FastAPI)                          │
│                                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐           │
│  │ Module 1    │ │ Module 2   │ │ Module 3   │           │
│  │ OCR (Rapid) │ │ Validation │ │ Tampering  │           │
│  │ + MRZ/CS   │ │ (Checksum) │ │ (OpenCV+ELA)│           │
│  └────────────┘ └────────────┘ └────────────┘           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │            Module 4: Face (InsightFace)             │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Risk Scoring Engine (weighted)         │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │     PostgreSQL / SQLite + Audit Trail               │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────┘
```

## Modules

1. **Module 1: OCR Extraction** — RapidOCR (ONNX PaddleOCR port). Extracts name, passport number, nationality, DOB, expiry, gender, etc. Includes full **MRZ parser** for TD1/TD2/TD3 formats with **ICAO 9303 checksum validation** (document number, DOB, expiry, composite checksums). Falls back to EasyOCR, then tesseract.

2. **Module 2: Document Validation** — Validates passport number format by country, date validity, expiry, name, gender, and **MRZ checksum** verification (detects forged/altered document numbers).

3. **Module 3: Tampering Detection (Core AI)** — OpenCV + Error Level Analysis plus:
   - Error Level Analysis (ELA) for digital manipulation
   - Noise distribution inconsistency
   - Copy-move forgery detection
   - Edge splicing irregularity
   - Stamp forgery analysis
   - Image metadata forensics

4. **Module 4: Face Verification** — InsightFace (ArcFace) face embeddings with opencv Haar fallback. Compares document photo vs live capture.

5. **Risk Engine** — Weighted 0–100 risk score. Weights: Tampering 40%, Validation 30%, Face 30%.

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt

# Optional: set PostgreSQL URL (defaults to SQLite for dev)
export DATABASE_URL=postgresql://user:pass@localhost/db

uvicorn app.main:app --reload     # or run start.bat
```

### Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.example .env.local        # set API_BASE_URL=http://localhost:8000
npm run dev                       # http://localhost:3000
```

### Docker (optional)

```bash
docker-compose up --build
# frontend: http://localhost:3000
# backend:  http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/screening/documents?document_type=passport` | Upload + screen a document |
| GET | `/api/screening/results` | All screening results |
| GET | `/api/screening/{id}` | Specific screening result |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| POST | `/api/screening/{id}/decision` | Decision on a document |
| GET | `/health` | Health check |

## Document Types

Passport · Visa · National ID · Driving License

## Risk Levels

| Level | Range | Action |
|-------|-------|--------|
| Low | 0–30 | Cleared |
| Medium | 30–60 | Manual review |
| High | 60–80 | Flagged |
| Critical | 80–100 | Immediate rejection |

## PaddleOCR Alternative

RapidOCR (`rapidocr-onnxruntime`) is an ONNX Runtime port of PaddleOCR that provides the same detection/recognition accuracy without the heavy `paddlepaddle` dependency. It's lighter, installs via pip on CPU, and runs fast at the edge. EasyOCR is bundled as a fallback backend.
