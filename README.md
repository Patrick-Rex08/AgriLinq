# AgriLink — Production Deployment Guide (Vercel + Cloud Backend)

AgriLink is an AI-powered, blockchain-enabled direct agricultural marketplace prototype built for the **Smart India Hackathon (SIH 2026)**.

---

## 📁 Repository Structure

```text
AgriLink-Vercel-Ready/
├── vercel.json                 # Vercel configuration with SPA client-side routing rewrites
├── package.json                # Root monorepo script coordinator
├── .gitignore                  # Prevents secrets, node_modules, and virtualenvs from leaking
├── .env.example                # Safe environment variable template
│
├── frontend/                   # React 19 + TypeScript + Vite + Tailwind CSS v4
│   ├── index.html              # Main HTML entry
│   ├── package.json            # Frontend dependencies
│   ├── vite.config.ts          # Vite build config
│   ├── vercel.json             # Subdirectory SPA routing rewrites
│   ├── .env.example            # Frontend environment variable guide
│   └── src/                    # Components across all 6 phases
│
└── backend/                    # Python FastAPI + SQLAlchemy + Uvicorn
    ├── requirements.txt        # Production Python dependencies
    ├── Procfile                # Standard cloud process runner (Render / Railway)
    ├── render.yaml             # Render 1-click cloud service blueprint
    ├── Dockerfile              # Container deployment file
    ├── seed.py                 # Automated demonstration database seeder
    └── app/                    # REST API routers, models, and services
```

---

## 🚀 Quick Local Testing

### 1. Test Frontend Build
```bash
cd frontend
npm install
npm run build
```
The build should complete in less than 1 second, outputting clean static assets to `frontend/dist/`.

### 2. Run Locally
**Terminal 1 (Backend):**
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```
Open **http://localhost:5173** in your browser.

---

## 🌐 Production Deployment Architecture

Because AgriLink contains both a **React 19 single-page frontend** and an **asynchronous Python FastAPI backend with persistent SQLite/PostgreSQL**, the industry-standard deployment architecture is:

1. **Frontend $\to$ Vercel**: High-speed global edge network for static assets and React UI.
2. **Backend $\to$ Render / Railway (Free Tier)**: Python container running `uvicorn app.main:app` with persistent database connectivity.
3. **Database $\to$ Cloud PostgreSQL (e.g. Neon.tech / Supabase)**: Free managed PostgreSQL instance.

---


- [x] **No Hardcoded Localhost**: `frontend/src/services/api.ts` dynamically uses `VITE_API_URL` without double slashes.
- [x] **No Secrets Committed**: `.gitignore` strictly protects `.env`, virtual environments, and database files.
- [x] **All 6 SIH Phases Active**: Marketplace, Farmer Dashboard, Buyer Orders, Phase 4 AI Market Intelligence, Phase 5 Logistics Hub, and Phase 6 Blockchain Provenance Ledger are included.
