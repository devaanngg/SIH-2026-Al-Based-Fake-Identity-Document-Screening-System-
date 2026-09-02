# HOW TO RUN THIS PROGRAM ON YOUR MACHINE (Windows)

This guide walks you through getting the AI Document Screening System running.

---

## WHAT YOU NEED

| Tool | Status on your machine | Needed for |
|------|----------------------|-----------|
| Python 3.13 | ✅ Already installed | Backend (FastAPI + AI) |
| Node.js + npm | ❌ NOT installed | Frontend (Next.js) |
| Tesseract OCR | Optional | Extra OCR fallback (not required) |

---

## STEP 1 — Install Node.js (one time)

The web interface needs Node.js which is NOT on your machine yet.

1. Go to: https://nodejs.org
2. Download the **LTS** version (left button, e.g. "20.x LTS")
3. Run the installer — click Next/Next/Install (accept defaults)
4. Restart your terminal / PowerShell

Verify it worked:
```
node --version
npm --version
```
You should see version numbers, not errors.

---

## STEP 2 — Run the BACKEND

The backend does all the AI work (OCR, tampering detection, MRZ checksum, risk scoring).

Open PowerShell, then:

```
cd "C:\Users\ashuk\OneDrive\ドキュメント\Default Project\backend"
python -m uvicorn app.main:app --reload
```

You should see output ending with:
`Uvicorn running on http://127.0.0.1:8000`

**Leave this window OPEN and running.**

You can verify it's alive by opening http://127.0.0.1:8000/health in your browser — it should show `{"status":"healthy"}`.

> Note: I already installed the Python packages (fastapi, opencv, rapidocr, sqlalchemy, etc.) for you earlier, so this should just work. If you ever get "ModuleNotFoundError", run:
> ```
> pip install -r requirements.txt
> ```

---

## STEP 3 — Run the FRONTEND (requires Node.js from Step 1)

Open a SECOND PowerShell window, then:

```
cd "C:\Users\ashuk\OneDrive\ドキュメント\Default Project\frontend"
npm install
npm run dev
```

The first `npm install` downloads all frontend packages (takes a few minutes first time).

When done you'll see:
`Ready in ...` and `http://localhost:3000`

---

## STEP 4 — USE IT

1. Open your browser to **http://localhost:3000**  ← the web interface
2. Go to **"New Screening"**
3. Pick a document type (Passport, Visa, National ID, Driving License)
4. Upload an image of the document, click **"Start Screening"**

You'll see the AI analysis:
- Extracted data (name, passport number, DOB, etc.)
- Doc validation (incl. MRZ checksum check)
- Tampering score
- Face match
- Final **risk score** and **risk level** (low/medium/high/critical)

The **Dashboard** shows stats, and **Screening History** lists everything processed.

---

## QUICK START ALTERNATIVE (backend + built-in web UI)

If you DON'T want to install Node.js right now, there's a simpler path —
the backend already includes a built-in web interface at:

```
http://localhost:8000
```

Just run Step 2 and open http://localhost:8000 — you get the same Dashboard,
Screening, and History, served directly by the backend (no Node needed).

Do Step 1–4 if you want the prettier Next.js interface.

---

## COMMON PROBLEMS

**"python is not recognized"**
→ Python isn't in PATH. Reinstall Python and tick "Add Python to PATH".

**"ModuleNotFoundError: No module named 'fastapi'"**
→ `pip install -r requirements.txt` (run in the `backend` folder)

**Port already in use**
→ Change ports:
   - Backend: use `--port 8001`
   - Frontend: next.config.js uses `API_BASE_URL=http://localhost:8000` — update to match

**Frontend can't reach backend**
→ Make sure the backend (Step 2) is still running, and both use the same host.
   The frontend proxies `/api` to `http://localhost:8000`.

---

## DOCKER (optional, if you have Docker Desktop)

If Docker is installed, the whole system (PostgreSQL + backend + frontend) starts with:

```
cd "C:\Users\ashuk\OneDrive\ドキュメント\Default Project"
docker-compose up --build
```

Frontend: http://localhost:3000   Backend: http://localhost:8000
