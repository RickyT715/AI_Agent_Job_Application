# AI Job Application Agent

An end-to-end AI-powered system that scrapes job boards, matches postings against your resume, generates cover letters and reports, and auto-fills applications with human-in-the-loop approval.

Uses **Gemini 3.1 Pro** for cheap tasks (parsing, extraction) and **Claude Sonnet 4.6** for reasoning tasks (scoring, cover letters, browser agent). Embeddings via **Gemini embedding-001**.

## Architecture

```
Resume Upload ──► Scrape Jobs ──► Match & Score ──► Generate Reports ──► Auto-Fill Application
                      │                │                   │                      │
                  JSearch API      ChromaDB +          Jinja2 HTML +         LangGraph agent
                  Greenhouse       FlashRank            Claude cover         with interrupt()
                  Lever            reranking +          letters              for human review
                                   Claude LLM-
                                   as-Judge
```

### Model Routing

| Task | Model | Why |
|------|-------|-----|
| Resume/job parsing, keyword extraction | `gemini-3.1-pro-preview` | Latest reasoning model |
| Embedding generation | `gemini-embedding-001` | Flexible dimensions, MRL |
| Match scoring (LLM-as-Judge) | `claude-sonnet-4-6` | Superior reasoning |
| Cover letter generation | `claude-sonnet-4-6` | Natural writing |
| Browser agent reasoning | `claude-sonnet-4-6` | Complex decision-making |

### Matching Pipeline

1. **Vector similarity** - top-30 candidates from ChromaDB via cosine similarity (Gemini embedding-001)
2. **Cross-encoder reranking** - FlashRank narrows to top-10 (local CPU, free)
3. **LLM-as-Judge scoring** - Claude scores each on skills/experience/education/location/salary (1-10)

## Project Structure

```
AI_Agent_Job_Application/
├── backend/                         # Python 3.13 + FastAPI
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Two-tier config (env + YAML)
│   │   ├── models/                  # SQLAlchemy ORM (6 tables)
│   │   ├── schemas/                 # Pydantic request/response
│   │   ├── routers/                 # API endpoints
│   │   ├── services/
│   │   │   ├── llm_factory.py       # Gemini/Claude model routing
│   │   │   ├── matching/            # Embed → retrieve → rerank → score
│   │   │   ├── scraping/            # JSearch, Greenhouse, Lever, Workday
│   │   │   ├── agent/               # LangGraph browser agent + ATS strategies
│   │   │   └── reports/             # PDF/HTML reports + cover letters
│   │   ├── mcp/                     # MCP server (FastMCP)
│   │   └── worker/                  # ARQ background tasks
│   ├── tests/                       # 364 tests
│   ├── Dockerfile                   # Multi-stage (api + worker)
│   └── pyproject.toml
├── frontend/                        # React 19 + TypeScript + Vite
│   ├── src/
│   │   ├── components/              # JobCard, ReviewDialog, ScoreRadarChart, etc.
│   │   ├── stores/                  # Zustand (app-store, agent-store)
│   │   ├── hooks/                   # TanStack Query + WebSocket hooks
│   │   └── pages/                   # Dashboard, Settings
│   ├── Dockerfile                   # Build + Nginx
│   └── vitest.config.ts
├── docker-compose.yml               # 5 services
├── .github/workflows/ci.yml         # GitHub Actions CI
└── .env.example
```

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 22+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker & Docker Compose (for full deployment)

### 1. Clone and Configure

```bash
git clone <repo-url>
cd AI_Agent_Job_Application
cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend Setup

```bash
cd backend
uv sync --dev
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Run Tests

```bash
# Backend (from backend/)
uv run pytest -m "not integration and not docker" -q

# Frontend (from frontend/)
npx vitest run
```

### 5. Run the App (Development)

```bash
# Terminal 1: Backend
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open http://localhost:5173 for the dashboard. API docs at http://localhost:8000/docs.

### 6. Run with Docker

```bash
docker compose up -d
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/config/resume` | Upload resume (multipart) |
| `GET/PUT` | `/api/config/preferences` | User preferences |
| `GET` | `/api/jobs` | List jobs (paginated, filterable) |
| `GET` | `/api/jobs/{id}` | Get job details |
| `POST` | `/api/jobs/scrape` | Trigger job scraping |
| `GET` | `/api/matches` | List scored matches (sorted by score) |
| `GET` | `/api/matches/{id}` | Match detail with breakdown |
| `POST` | `/api/matches/run` | Trigger matching pipeline |
| `POST` | `/api/reports/generate` | Generate PDF report |
| `POST` | `/api/reports/cover-letter` | Generate cover letter |
| `POST` | `/api/agent/start` | Start browser agent |
| `POST` | `/api/agent/resume/{id}` | Resume agent (approve/reject/edit) |
| `WS` | `/ws/agent-status` | Real-time agent progress |

## MCP Server

The project includes an MCP server for integration with Claude Desktop, Cursor, or other MCP clients.

### Tools

| Tool | Description |
|------|-------------|
| `search_jobs` | Search job postings with location/query filters |
| `match_resume_to_jobs` | Scrape + score jobs against current resume |
| `fill_application` | Preview or submit job application (dry_run default) |
| `generate_cover_letter` | Generate personalized cover letter |
| `generate_report` | Generate HTML match report |

### Resources

| URI | Description |
|-----|-------------|
| `resume://current` | Current resume text |
| `preferences://job-search` | Job search preferences (JSON) |

### Running the MCP Server

```bash
# stdio transport (for Claude Desktop / Cursor)
cd backend
uv run python -m app.mcp

# Streamable HTTP transport
uv run fastmcp run app.mcp.server:mcp --transport streamable-http --port 8001
```

## Browser Agent

The LangGraph-based browser agent handles job application form filling with human-in-the-loop approval.

```
START → detect_ats → [route]
  ├─ Greenhouse/Lever → api_submit → END (direct API, no browser needed)
  └─ Workday/Generic → navigate → fill_fields → upload_resume → answer_questions
                         → review_node (INTERRUPT: human approval)
                           ├─ approve → submit → END
                           ├─ reject  → abort  → END
                           └─ edit    → fill_fields (loop back)
```

The agent pauses at `review_node` using LangGraph's `interrupt()`, saves state, and shows the filled fields + screenshot in the dashboard for human review before submission.

## Configuration

### Infrastructure (`.env`)

```env
GOOGLE_API_KEY=...          # Gemini API (Gemini 3 requires paid tier)
ANTHROPIC_API_KEY=...       # Claude API
JSEARCH_API_KEY=...         # RapidAPI JSearch
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
```

### User Preferences (`backend/data/user_config.yaml`)

```yaml
job_titles:
  - Software Engineer
  - Backend Engineer
locations:
  - Remote
  - San Francisco
salary_min: 120000
salary_max: 200000
workplace_types:
  - remote
  - hybrid
experience_level: senior
weights:
  skills: 0.35
  experience: 0.25
  education: 0.15
  location: 0.15
  salary: 0.10
```

## Testing

### Test Summary

| Suite | Tests | Description |
|-------|------:|-------------|
| Matching (Phase 1) | 55 | LLM factory, embedder, retriever, scorer, pipeline, config |
| Scraping (Phase 2) | 56 | JSearch, Greenhouse, Lever, normalizer, dedup, orchestrator |
| DB & API (Phase 3) | 47 | Models, routers, WebSocket, ARQ tasks |
| Agent (Phase 4) | 71 | State, graph routing, field mapper, ATS, interrupt/resume |
| Reports (Phase 6) | 52 | PDF generator, cover letter, templates, evaluation |
| MCP (Phase 7) | 22 | Tools, resources, prompts |
| Docker (Phase 7) | 21 | Compose validation |
| Integration | 31 | Full user workflow (9 steps) |
| Frontend | 36 | Components, stores (Vitest + RTL + MSW) |
| **Total** | **397** | |

### Running Tests

```bash
# All backend unit tests (excludes integration tests needing real APIs)
cd backend
uv run pytest -m "not integration and not docker" -q

# Full backend suite (includes integration tests)
uv run pytest -v

# Specific phase
uv run pytest tests/test_matching/ -v     # Phase 1
uv run pytest tests/test_scraping/ -v     # Phase 2
uv run pytest tests/test_agent/ -v        # Phase 4
uv run pytest tests/test_reports/ -v      # Phase 6
uv run pytest tests/test_mcp/ -v          # Phase 7

# User workflow integration test
uv run pytest tests/test_integration/test_user_workflow.py -v

# Frontend
cd frontend
npx vitest run
```

### User Workflow Test

`test_user_workflow.py` simulates the complete real-user journey with mocked external APIs but real internal code paths:

1. **Resume & Config** - Upload resume, configure preferences
2. **Job Scraping** - Orchestrate scrapers, deduplicate
3. **Job Storage** - Store in DB, verify API retrieval with pagination
4. **Matching** - Score with LLM-as-Judge, verify sorted results + filtering
5. **Reports** - Generate HTML reports (high/low scores), cover letters
6. **Evaluation** - F1 skill matching, score accuracy metrics
7. **Browser Agent** - Full LangGraph cycle: detect ATS, fill, interrupt, approve/reject
8. **MCP Server** - Tools, resources, dry-run application
9. **Docker** - Compose validation, CI workflow

## Tech Stack

### Backend
- **Python 3.13** with **uv** package manager
- **FastAPI** + uvicorn (async web framework)
- **SQLAlchemy 2.0** + asyncpg/aiosqlite (async ORM)
- **LangChain** + LangGraph (AI orchestration)
- **ChromaDB** (vector store) + **FlashRank** (reranking)
- **ARQ** (async Redis task queue)
- **Jinja2** (HTML report templates)
- **FastMCP** (MCP server)

### Frontend
- **React 19** + **TypeScript** + **Vite**
- **Zustand** (UI state) + **TanStack Query v5** (server state)
- **Recharts** (radar charts)
- **react-use-websocket** (real-time agent updates)
- **Tailwind CSS**

### Infrastructure
- **PostgreSQL 16** (primary database)
- **Redis 7** (task queue)
- **Docker Compose** (5-service deployment)
- **GitHub Actions** (CI/CD)
- **Nginx** (frontend reverse proxy)

## License

MIT
