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

## 📤 Step-by-Step Deployment Instructions

### STEP 1: Upload to a NEW GitHub Repository

1. Open your terminal inside this `AgriLink-Vercel-Ready` folder:
   ```bash
   cd AgriLink-Vercel-Ready
   ```
2. Initialize a clean Git repository:
   ```bash
   git init -b main
   ```
3. Add all files and make your initial commit:
   ```bash
   git add .
   git commit -m "feat: initial commit of production Vercel-ready AgriLink"
   ```
4. Create a **New Repository** on GitHub (named e.g. `agrilink-platform`).
   *(Do NOT initialize with a README or .gitignore on GitHub since we already have them).*
5. Link your local repo to GitHub and push:
   ```bash
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/agrilink-platform.git
   git push -u origin main
   ```

---

### STEP 2: Deploy Backend on Render (Free 5-Minute Setup)

1. Go to [Render.com](https://render.com) and sign in with GitHub.
2. Click **New +** $\to$ **Web Service**.
3. Select your `agrilink-platform` repository.
4. Fill in the following settings:
   - **Name:** `agrilink-api`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   - `ENVIRONMENT` = `production`
   - `BACKEND_CORS_ORIGINS` = `["*"]`
   - *(Optional)* `DATABASE_URL` = your PostgreSQL database connection string (e.g., from [Neon.tech](https://neon.tech)). If omitted, it will automatically run with a local SQLite database.
6. Click **Deploy Web Service**.
7. Once deployed, copy your backend URL:
   `https://agrilink-api.onrender.com`

---

### STEP 3: Deploy Frontend on Vercel (Zero 404s)

1. Go to [Vercel.com](https://vercel.com) and click **Add New...** $\to$ **Project**.
2. Import your GitHub repository (`agrilink-platform`).
3. In the Vercel **Configure Project** screen:
   - **Framework Preset:** `Vite`
   - **Root Directory:**
     - You can leave it as `./` (the root `vercel.json` will automatically build the frontend), **OR** click "Edit" and select `frontend`. Both methods will build successfully!
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Expand **Environment Variables** and add:
   - **Key:** `VITE_API_URL`
   - **Value:** `https://agrilink-api.onrender.com/api`
     *(Replace with your actual Render backend URL from Step 2, appending `/api`)*
5. Click **Deploy**.
6. Vercel will build the frontend in ~20 seconds. Click on the generated domain (e.g. `https://agrilink-platform.vercel.app`) to view your live application!

---

## 🛠️ Verification Checklist for Vercel

- [x] **No Root 404**: `vercel.json` contains `"rewrites": [{"source": "/(.*)", "destination": "/index.html"}]` to prevent 404s on page refresh.
- [x] **No Hardcoded Localhost**: `frontend/src/services/api.ts` dynamically uses `VITE_API_URL` without double slashes.
- [x] **No Secrets Committed**: `.gitignore` strictly protects `.env`, virtual environments, and database files.
- [x] **All 6 SIH Phases Active**: Marketplace, Farmer Dashboard, Buyer Orders, Phase 4 AI Market Intelligence, Phase 5 Logistics Hub, and Phase 6 Blockchain Provenance Ledger are included.
