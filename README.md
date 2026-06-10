# OSCA — Open Source Contribution Agent

A multi-agent AI platform that helps developers discover, understand, and contribute to open-source projects by matching them with suitable GitHub issues based on their skills and experience.

## Features

- **GitHub OAuth** — authenticate and analyze your developer profile
- **Skill-Issue Matching** — Sentence Transformers (`all-MiniLM-L6-v2`) + cosine similarity
- **Difficulty Prediction** — heuristic classifier (easy / medium / hard)
- **Gemini Explanations** — LLM-powered match reasons and PR review
- **LangGraph Multi-Agent Workflow** — Profile → Discovery → Matching → Codebase → Learning Gaps
- **Bookmarks & Analytics** — save issues and track agent runs

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, SQLite/PostgreSQL |
| ML | Sentence Transformers, scikit-learn |
| LLM | Google Gemini API |
| Agents | LangGraph |
| Vector DB | Qdrant (optional) |
| Frontend | HTML + Tailwind CSS |

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python download_model.py
cp ../.env.example ../.env    # fill in your keys
uvicorn main:app --reload
```

### 2. Frontend

Serve `frontend/index.html` with any static server (e.g. VS Code Live Server on port 5500):

```bash
# Set FRONTEND_URL=http://127.0.0.1:5500 in .env
```

### 3. GitHub OAuth Setup

1. Create an OAuth App at https://github.com/settings/developers
2. Set callback URL to `http://localhost:8000/api/v1/auth/callback`
3. Add `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` to `.env`

### 4. Gemini API

Get a key at https://aistudio.google.com/apikey and set `GEMINI_API_KEY` in `.env`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/auth/login` | GitHub OAuth redirect |
| GET | `/api/v1/auth/me` | Current user |
| GET | `/api/v1/profile/analyze` | Analyze GitHub profile |
| GET | `/api/v1/recommendations/issues` | Ranked issue recommendations |
| POST | `/api/v1/agents/match` | Run full LangGraph workflow |
| POST | `/api/v1/agents/pr-review` | PR diff review |
| GET | `/api/v1/analytics/dashboard` | User analytics |
| GET/POST | `/api/v1/bookmarks` | Bookmark management |

Full docs at `http://localhost:8000/docs`.

## Docker

```bash
docker compose up --build
```

## Project Structure

```
backend/
├── main.py                 # FastAPI entrypoint
├── app/
│   ├── api/v1/             # REST routers
│   ├── agents/             # LangGraph workflow
│   ├── services/           # Business logic
│   ├── models/             # SQLAlchemy models
│   └── core/               # Config, auth, database
frontend/
└── index.html              # Dashboard UI
```

## License

MIT
