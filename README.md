# Multimodal Construction Intelligence Platform

Multimodal AI decision-support platform for site engineers, contractors, and project managers. Powered by **Groq** vision and text models.
Available in two deployment flavors:
1. **Streamlit App (`streamlit_app.py`)**: Standalone pure-Python app ready for **Streamlit Community Cloud** ([Deployment Guide](STREAMLIT_DEPLOYMENT.md)).
2. **Full-Stack App**: **FastAPI** backend + **React 18 / Vite** frontend.

All financial outputs and cost calculations are localized to **Indian Rupees (₹ / INR)**.

---

## Repository Structure

```text
Multimodal-Construction-Intelligence-Platform/
├── .streamlit/                 # Streamlit Cloud configuration & secrets template
│   ├── config.toml             # Theme (Dark/Amber) & server configuration
│   └── secrets.toml.example    # Secrets template for GROQ_API_KEY
├── streamlit_app.py            # Standalone Streamlit App (Deploy on Streamlit Cloud)
├── requirements.txt            # Root dependencies for Streamlit Cloud
├── STREAMLIT_DEPLOYMENT.md     # Step-by-step Streamlit Cloud deployment guide
├── .env.example                # Legacy root placeholder template
├── .gitignore                  # Git ignore rules (.env, .venv, node_modules)
├── README.md                   # Project documentation
├── backend/                    # FastAPI application
│   ├── .env                    # Real secrets (git-ignored)
│   ├── .env.example            # Backend environment template
│   ├── ai_service.py           # Centralized Groq SDK integration
│   ├── config.py               # Pydantic BaseSettings loader
│   ├── main.py                 # FastAPI routes, schemas, and error handlers
│   ├── pyproject.toml          # Pytest, coverage, and Pyright configuration
│   ├── requirements.txt        # Backend dependencies
│   ├── schemas.py              # Pydantic v2 response schemas
│   └── tests/                  # Backend pytest test suite
│       ├── conftest.py         # Shared test fixtures (TestClient)
│       ├── test_ai_service.py  # Groq AI service & error handling tests
│       ├── test_api.py         # API route & validation tests
│       └── test_schemas.py     # Pydantic schema validation tests
└── frontend/                   # React 18 + Vite SPA
    ├── .env                    # Real frontend config (git-ignored, optional)
    ├── .env.example            # Frontend environment template
    ├── package.json            # Frontend dependencies and scripts
    ├── vite.config.js          # Vite config with /api proxy to backend
    └── src/
        ├── App.jsx             # Root layout and client routing
        ├── api.js              # Axios HTTP client with INR currency formatters
        ├── index.css           # Core design system and dark theme styling
        ├── main.jsx            # Application mount point
        ├── components/         # Reusable UI components
        │   ├── ImageUploader.jsx
        │   ├── ResultCards.jsx
        │   ├── ScoreGauge.jsx
        │   └── Sidebar.jsx
        └── pages/              # Module page components
            ├── AIChat.jsx
            ├── CostEstimation.jsx
            ├── Dashboard.jsx
            ├── MaterialAnalysis.jsx
            ├── ProgressMonitoring.jsx
            ├── ProjectReport.jsx
            ├── SafetyInspection.jsx
            ├── SiteAnalysis.jsx
            └── VisualProgress.jsx
```

---

## Environment Configuration

The repository uses separate environment files for the backend and frontend. The committed `.env.example` files are templates; real `.env` files are ignored by Git.

### Backend (`backend/.env`)

The backend loads settings directly from `backend/.env` using Pydantic Settings. Create this file from `backend/.env.example`:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | Yes (for AI) | `""` | Groq API key (starts with `gsk_`). Get a key at [console.groq.com](https://console.groq.com). |
| `GROQ_TEXT_MODEL` | No | `openai/gpt-oss-120b` | Supported Groq model for text queries and estimations. |
| `GROQ_VISION_MODEL` | No | `qwen/qwen3.8-27b` | Supported Groq multimodal vision model for image inspections. |
| `GROQ_BASE_URL` | No | None (`https://api.groq.com`) | Optional custom Groq API base URL. |
| `PORT` | No | `8000` | Port for the backend server. |
| `APP_ENV` | No | `development` | Environment label (`development` or `production`). |
| `ALLOWED_ORIGINS` | No | `http://localhost:5173,http://localhost:3000` | Comma-separated list of exact browser origins permitted by CORS. Wildcards (`*`) are rejected. |
| `MAX_IMAGE_SIZE_MB` | No | `10` | Maximum upload size for multimodal endpoints in megabytes (range: 1–50). |

### Frontend (`frontend/.env`)

A frontend `.env` file is **optional** for local development because `vite.config.js` automatically proxies `/api` requests to `http://127.0.0.1:8000`. If overriding the defaults:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `VITE_API_BASE_URL` | No | `/api` | Base URL path for API requests made by the browser. |
| `VITE_API_PROXY_TARGET` | No | `http://127.0.0.1:8000` | Target URL used by the Vite development server proxy. |

> **Note on Root `.env.example`**: The `.env.example` file in the repository root is a legacy placeholder. The backend strictly reads `backend/.env`.

---

## Prerequisites

- **Python**: 3.10 to 3.12 (Python 3.11+ recommended)
- **Node.js**: 18.0 or newer and `npm`
- **Groq API Key**: Free API key from [console.groq.com](https://console.groq.com)

---

## Setup Guide

Run commands from the repository root.

### Windows (PowerShell)

```powershell
# 1. Create backend environment configuration
Copy-Item backend/.env.example backend/.env
# Open backend/.env in an editor and set GROQ_API_KEY=gsk_your_key_here

# 2. Create and configure backend virtual environment
python -m venv backend/.venv

# Activate the virtual environment
# (If script execution is disabled, first run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned)
.\backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Install frontend dependencies
Set-Location frontend
npm install
Set-Location ..
```

*Tip: You can also execute backend commands directly without activating the virtual environment by using `.\backend\.venv\Scripts\python.exe`.*

### macOS / Linux

```bash
# 1. Create backend environment configuration
cp backend/.env.example backend/.env
# Open backend/.env in an editor and set GROQ_API_KEY=gsk_your_key_here

# 2. Create and configure backend virtual environment
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## Running the Application

Start the backend and frontend in two separate terminals from the repository root.

### Terminal 1 — Backend

**Windows (PowerShell):**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --port 8000
```
*(Or without activating: `.\backend\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000` from `backend`)*

**macOS / Linux:**
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

The backend server starts on `http://localhost:8000`.
- Swagger UI Documentation: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health` (and `http://localhost:8000/api/health`)

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

The frontend development server starts on `http://localhost:5173`. Requests to `/api/*` are automatically proxied to `http://127.0.0.1:8000`.

---

## AI Models

The backend integrates Groq models through the official Python SDK:

| Workload | Model Identifier | Input Type | Used In |
| --- | --- | --- | --- |
| **Multimodal Vision** | `qwen/qwen3.8-27b` | Base64 Image + Structured Prompt | Site Analysis, Safety Inspection, Visual Progress |
| **Text Generation** | `openai/gpt-oss-120b` | Text / Structured Prompt | Cost Estimation, Material Analysis, Progress Monitoring, Project Reports, AI Chat |

Model IDs are configurable via `GROQ_VISION_MODEL` and `GROQ_TEXT_MODEL` in `backend/.env`.

All responses are validated against strict Pydantic v2 schemas. If the AI provider returns an invalid payload or is unreachable, the API returns a structured HTTP 502 error rather than unverified placeholder data.

---

## API Endpoints

| Method | Path | Request Body | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | None | Service liveness and Groq availability check. |
| `GET` | `/api/health` | None | Frontend API client health check alias. |
| `POST` | `/api/site-analysis` | `multipart/form-data` (`image`) | Visual site condition evaluation, hazard identification, and structural observations. |
| `POST` | `/api/safety-inspection` | `multipart/form-data` (`image`) | PPE compliance check, safety hazard detection, and safety score (1–100). |
| `POST` | `/api/visual-progress` | `multipart/form-data` (`image`, `expected_stage`, `notes`) | Stage completion estimation and visual quality inspection. |
| `POST` | `/api/cost-estimation` | `application/x-www-form-urlencoded` | Project cost estimate with server-calculated line item amounts in INR (₹). |
| `POST` | `/api/material-analysis` | `application/x-www-form-urlencoded` | Bill of Quantities (BOQ) with material breakdown and total costs in INR (₹). |
| `POST` | `/api/progress-monitoring` | `application/x-www-form-urlencoded` | Earned Value Management (EVM) metrics: SV, CV, SPI, CPI, and schedule variance. |
| `POST` | `/api/project-report` | `application/x-www-form-urlencoded` | Executive progress report, milestone timeline, risk log, and recommendations. |
| `POST` | `/api/chat` | `application/json` (`{"message": "..."}`) | Construction knowledge Q&A assistant (single-turn). |

---

## Feature Scope & Implementation Details

| Feature Area | Current Implementation Status |
| --- | --- |
| **Site Safety & PPE Screening** | Implemented at `/api/safety-inspection`. Analyzes uploaded images for PPE compliance and site hazards. Preliminary screening only; professional verification is required. |
| **Structural Observation** | Implemented as part of `/api/site-analysis`. Identifies visible structural distress from uploaded photos. Does not replace certified non-destructive testing or structural engineering evaluations. |
| **Construction Cost Estimation** | Implemented at `/api/cost-estimation`. Generates indicative Bill of Quantities based on user inputs. Line items and totals are computed and verified server-side in Indian Rupees (₹). Not a binding contractor quote. |
| **Material BOQ Estimation** | Implemented at `/api/material-analysis`. Estimates material requirements (cement, steel, aggregate, finishes) with server-calculated totals. Does not connect to live supplier price feeds. |
| **Progress & EVM Monitoring** | Implemented at `/api/progress-monitoring`. Computes Schedule Variance (SV), Cost Variance (CV), SPI, and CPI from reported progress and expenditure figures. |
| **Executive Project Reporting** | Implemented at `/api/project-report`. Compiles status, KPIs, risks, and forecasts into a structured summary. |
| **Construction Knowledge Chat** | Implemented at `/api/chat`. Single-turn question-and-answer assistant for civil engineering and construction queries. |
| **Real Estate Valuation** | Not implemented. |
| **Weather Advisories** | Not implemented (no third-party weather API integrated). |

---

## Testing & Quality Assurance

### Backend Tests

The backend test suite includes 35 tests covering schemas, route handlers, error cases, and Groq service integration:

```bash
cd backend
# With virtual environment activated:
pytest

# Or via Python directly from the repository root:
# Windows:
.\backend\.venv\Scripts\python.exe -m pytest backend
# macOS/Linux:
./backend/.venv/bin/python -m pytest backend
```

### Frontend Build & End-to-End Tests

```bash
cd frontend

# Verify production bundle build
npm run build

# Install Playwright browser dependencies (one-time)
npm run test:e2e:install

# Run end-to-end tests (runs against a mock server; no Groq key required)
npm run test:e2e
```

---

## Deployment Considerations

- **Separate Hosting**: Deploy the FastAPI backend (e.g., Render, Railway, AWS ECS) and Vite frontend (e.g., Vercel, Netlify, Cloudflare Pages) as decoupled services.
- **CORS Configuration**: Set `ALLOWED_ORIGINS` in `backend/.env` to the exact public frontend domain(s). Do not use wildcards (`*`).
- **Production API URL**: Set `VITE_API_BASE_URL` in `frontend/.env` to the public backend origin (including `/api`) before running `npm run build`.
- **Secrets Management**: Keep `GROQ_API_KEY` strictly on the backend. Never prefix secrets with `VITE_` or expose them in the frontend bundle.
- **Reverse Proxy & Request Limits**: Ensure upstream reverse proxies (Nginx, Cloudflare, etc.) permit file uploads matching `MAX_IMAGE_SIZE_MB` (default: 10 MB).
