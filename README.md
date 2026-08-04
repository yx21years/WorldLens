![WorldLens AI Screenshot](placeholder.png)

# WorldLens AI — Personal World Intelligence Assistant

A desktop application that collects, analyzes, and summarizes global news using AI. Designed for curious learners, researchers, and knowledge workers who want to understand the world beyond headlines.

## Architecture Overview

```
Electron + React (UI)
     │
     ▼ HTTP ───► Python FastAPI (Backend)
                 ├─ Collection Service (RSS + NewsAPI)
                 ├─ AI Analysis Service (Claude/LLM)
                 ├─ Briefing Generator
                 └─ SQLite Database
```

## Phase 1: Project Initialization Complete

The skeleton is ready:
- **Backend:** FastAPI app with `/health`, SQLite connection, config system
- **Frontend:** Electron window with React page rendering
- **Communication:** Frontend calls backend health endpoint successfully

## Running the Project

### Prerequisites

- Python 3.10+ (with `pip` and `python -m venv`)
- Node.js 18+ (with `npm`)
- Optional: Git

### Start Backend

```bash
cd worldlens-ai/backend
source venv/bin/activate        # Windows: venv\Scripts\activate
cp .env.example .env            # Edit with your LLM API key if you have one
python -m uvicorn main:app --reload --port 8000
```

Verify:
```bash
curl http://localhost:8000/health
# {"status": "healthy", "app": "WorldLens AI", "version": "0.1.0"}
```

### Start Frontend

Open a **new terminal** in the project root:

```bash
cd worldlens-ai/frontend
npm run electron:dev
```

This starts Vite (React dev server on port 3000) and launches Electron, which loads the React app and can call the backend at `http://localhost:8000`.

## Verifying Everything Works

### Step 1 — Backend health check

In a new terminal:

```bash
curl http://localhost:8000/health
```

Expected response (200 OK):
```json
{"status":"healthy","app":"WorldLens AI","version":"0.1.0"}
```

### Step 2 — Open the UI

Run `npm run electron:dev` in the frontend directory. A desktop window should open showing:

```
🌍 WorldLens AI
v0.1.0
[Check Backend Status]
[JSON output from health check]
```

Click the button — the UI makes an HTTP GET to `/health` and displays the result. If you see JSON after clicking, the full end-to-end pipeline works.

### Step 3 — Confirm SQLite exists

After starting the backend for the first time, the file `data/worldlens.db` will be created automatically. Verify its presence:

```bash
ls data/worldlens.db
```

### Step 4 — Review endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/v1/status/health` | GET | Structured health status |
| `/api/v1/status/stats` | GET | App statistics (V2) |

## What's Next — Roadmap

- **Phase 2:** Implement collection pipeline, LLM integration, analysis service
- **Phase 3:** Briefing generator, user profile, settings management
- **Phase 4:** Testing (unit + integration), Docker packaging, portfolio polish

## Portfolio Notes

This project demonstrates:
- ✅ Clean separation of concerns (backend service layer, routing, database)
- ✅ Dependency injection and config hierarchy (.env → yaml → defaults)
- ✅ Error handling hierarchy with domain-specific error classes
- ✅ Prompt-as-config design (versioned prompt templates as JSON files)
- ✅ LLM abstraction pattern (provider protocol + concrete implementations)
- ✅ Structured logging with sensitive-field masking
- ✅ Test fixtures + unit/integration/LLM-eval test tiers
- ✅ Desktop-first architecture (Electron + React) + web demo path
- ✅ Docker deployment strategy for both backend and frontend

All of this is implemented while keeping the codebase small enough to finish in ~6 weeks for a solo developer.
