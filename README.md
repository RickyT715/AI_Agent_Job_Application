# AI Job Application Agent

An end-to-end AI-powered system that scrapes job boards, matches postings against your resume using a multi-stage pipeline, generates cover letters and reports, and auto-fills applications with human-in-the-loop approval.

Uses **Gemini 3.1 Pro** for cheap tasks (parsing, extraction) and **Claude Sonnet 4.6** for reasoning tasks (scoring, cover letters, browser agent). Embeddings via **Gemini embedding-001**. Matching pipeline includes heuristic pre-filtering, vector retrieval, cross-encoder reranking, LLM quick-scoring, and full multi-dimensional LLM-as-Judge evaluation.

## Architecture

```
Resume Upload ──► Scrape Jobs ──► Pre-Filter ──► Match & Score ──► Reports ──► Auto-Fill
                      │               │               │               │            │
                  JSearch API     Seniority/       ChromaDB +      Jinja2 HTML   LangGraph
                  Greenhouse     Location/Type    FlashRank +     + Claude       agent with
                  Lever          heuristics       Quick-Score +   cover letters  interrupt()
                  Adzuna                          Claude Full                    for human
                  Arbeitnow                       LLM-as-Judge                   review
```

### Model Routing

| Task | Model | Why |
|------|-------|-----|
| Resume/job parsing, keyword extraction | `gemini-3.1-pro-preview` | Latest reasoning model, cost-efficient |
| Embedding generation | `gemini-embedding-001` | Flexible dimensions, MRL |
| Quick-score relevance pre-screening | `claude-sonnet-4-6` | Fast triage of candidates |
| Full match scoring (LLM-as-Judge) | `claude-sonnet-4-6` | Superior multi-dimensional reasoning |
| Cover letter generation | `claude-sonnet-4-6` | Natural, tailored writing |
| Browser agent reasoning | `claude-sonnet-4-6` | Complex decision-making for form filling |

### Matching Pipeline (5-Stage)

```
Raw Jobs ──► Pre-Filter ──► Embed & Index ──► Retrieve ──► Quick-Score ──► Full-Score
  200         ↓ 35            ChromaDB         ↓ 30          ↓ 25           ↓ 25
              Seniority       Gemini emb.      Vector sim    Claude JSON    Claude
              Location        batch embed      + FlashRank   relevance      structured
              Emp. type                        rerank        1-10 triage    output
```

1. **Pre-filter** — `JobPreFilter` removes obviously irrelevant jobs using fast heuristics:
   - Seniority level matching (e.g., "mid" user rejects VP/Director/Principal titles)
   - Location compatibility (country keyword overlap; remote always passes)
   - Employment type filtering (FULLTIME/PARTTIME/CONTRACT normalization)
2. **Vector similarity** — Top-30 candidates from ChromaDB via cosine similarity using focused retrieval query (target title + skills + locations instead of raw resume)
3. **Cross-encoder reranking** — FlashRank narrows to top-10 (local CPU, free)
4. **Quick-score** — Claude rates relevance 1-10 with a lightweight prompt (500-char job brief, JSON response). Jobs below threshold 4 are skipped.
5. **Full LLM-as-Judge scoring** — Claude scores surviving candidates on skills/experience/education/location/salary (1-10 each) with explicit weight percentages from `MatchingWeights` config. Returns structured output with reasoning, strengths, missing skills, and interview talking points.

## Project Structure

```
AI_Agent_Job_Application/
├── backend/                             # Python 3.13 + FastAPI
│   ├── app/
│   │   ├── main.py                      # FastAPI entry point + middleware
│   │   ├── config.py                    # Two-tier config (env + YAML)
│   │   ├── models/                      # SQLAlchemy ORM (6 tables)
│   │   │   ├── user.py                  # User profile + resume text
│   │   │   ├── job.py                   # Normalized job postings
│   │   │   ├── match_result.py          # Score breakdowns + reasoning
│   │   │   ├── application.py           # Submitted application tracking
│   │   │   ├── cover_letter.py          # Generated cover letters
│   │   │   └── agent_log.py             # Browser agent step logs
│   │   ├── schemas/
│   │   │   ├── matching.py              # JobPosting, ScoreBreakdown, ScoredMatch
│   │   │   └── api.py                   # Request/response models, pagination
│   │   ├── routers/
│   │   │   ├── jobs.py                  # CRUD + scrape trigger
│   │   │   ├── matches.py               # Scoring results + pipeline trigger
│   │   │   ├── agent.py                 # Browser agent start/resume + WebSocket
│   │   │   ├── reports.py               # PDF/HTML report + cover letter
│   │   │   └── config.py                # Preferences + resume upload
│   │   ├── services/
│   │   │   ├── llm_factory.py           # Gemini/Claude model routing
│   │   │   ├── matching/
│   │   │   │   ├── pre_filter.py        # Seniority/location/type heuristics
│   │   │   │   ├── embedder.py          # ChromaDB indexing + Gemini embeddings
│   │   │   │   ├── retriever.py         # Vector search + FlashRank rerank
│   │   │   │   ├── scorer.py            # LLM-as-Judge (full + quick score)
│   │   │   │   └── pipeline.py          # 5-stage orchestrator
│   │   │   ├── scraping/
│   │   │   │   ├── base.py              # Abstract BaseScraper interface
│   │   │   │   ├── orchestrator.py      # Multi-source coordination + dedup
│   │   │   │   ├── normalizer.py        # Raw data → JobPosting schema
│   │   │   │   ├── deduplicator.py      # Cross-source duplicate removal
│   │   │   │   ├── api/                 # API-based scrapers
│   │   │   │   │   ├── jsearch.py       # RapidAPI JSearch
│   │   │   │   │   ├── greenhouse.py    # Greenhouse boards API
│   │   │   │   │   ├── lever.py         # Lever postings API
│   │   │   │   │   ├── adzuna.py        # Adzuna job board API
│   │   │   │   │   └── arbeitnow.py     # Arbeitnow public API
│   │   │   │   └── browser/             # Browser-based scrapers
│   │   │   │       ├── generic.py       # Playwright generic scraper
│   │   │   │       └── workday.py       # Workday-specific automation
│   │   │   ├── agent/
│   │   │   │   ├── graph.py             # LangGraph state machine
│   │   │   │   ├── state.py             # ApplicationState TypedDict
│   │   │   │   ├── nodes.py             # navigate, fill, review, submit nodes
│   │   │   │   ├── field_mapper.py      # Resume → form field mapping
│   │   │   │   └── ats/                 # ATS-specific strategies
│   │   │   │       ├── greenhouse.py    # Greenhouse API submit
│   │   │   │       └── lever.py         # Lever API submit
│   │   │   └── reports/
│   │   │       ├── generator.py         # PDF/HTML report generation
│   │   │       ├── cover_letter.py      # Claude-powered cover letters
│   │   │       ├── evaluation.py        # Match quality metrics
│   │   │       └── templates/
│   │   │           └── report.html      # Jinja2 report template
│   │   ├── mcp/
│   │   │   └── server.py                # FastMCP server (tools + resources)
│   │   └── worker/
│   │       └── tasks.py                 # ARQ background tasks
│   ├── tests/                           # 397+ tests across 65 files
│   │   ├── test_matching/               # Pipeline, pre-filter, scorer, embedder, retriever
│   │   ├── test_scraping/               # All 5 scrapers, dedup, normalizer, orchestrator
│   │   ├── test_agent/                  # Graph, nodes, ATS handlers, interrupts
│   │   ├── test_api/                    # All routers + WebSocket
│   │   ├── test_db/                     # Model CRUD + constraints
│   │   ├── test_reports/                # PDF, cover letter, evaluation
│   │   ├── test_mcp/                    # Tools, resources, prompts
│   │   ├── test_worker/                 # ARQ task tests
│   │   ├── test_docker/                 # Compose validation
│   │   ├── test_config/                 # Settings + UserConfig validation
│   │   ├── test_integration/            # Full user workflow (9-step)
│   │   └── e2e_pipeline_test.py         # Live scrape + score E2E test
│   ├── alembic/                         # Database migrations
│   ├── Dockerfile                       # Multi-stage (api + worker targets)
│   └── pyproject.toml                   # hatchling, ruff, mypy, pytest config
├── frontend/                            # React 19 + TypeScript + Vite 7
│   ├── src/
│   │   ├── App.tsx                      # Root with React Router v7
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx        # Main job listing + matching
│   │   │   └── SettingsPage.tsx         # Preferences + resume upload
│   │   ├── components/
│   │   │   ├── JobCard.tsx              # Job card with score badge
│   │   │   ├── JobList.tsx              # Paginated listing
│   │   │   ├── JobFilters.tsx           # Search + location + type filters
│   │   │   ├── MatchDetail.tsx          # Score breakdown + radar chart
│   │   │   ├── PreferencesForm.tsx      # Settings form
│   │   │   ├── ScoreRadarChart.tsx      # Recharts radar visualization
│   │   │   ├── SkillGapAnalysis.tsx     # Skill comparison matrix
│   │   │   ├── AgentProgress.tsx        # Real-time agent status
│   │   │   └── ReviewDialog.tsx         # Human-in-the-loop approval
│   │   ├── stores/
│   │   │   ├── app-store.ts             # Zustand (filters, selection)
│   │   │   └── agent-store.ts           # Agent execution state
│   │   ├── hooks/
│   │   │   ├── use-jobs.ts              # TanStack Query for jobs
│   │   │   ├── use-matches.ts           # TanStack Query for matches
│   │   │   └── use-agent-ws.ts          # WebSocket agent updates
│   │   └── api/
│   │       └── client.ts                # HTTP client config
│   ├── __tests__/                       # 36 Vitest tests (components + stores)
│   ├── Dockerfile                       # Build + Nginx
│   └── package.json
├── docker-compose.yml                   # 5 services (db, redis, backend, worker, frontend)
├── .github/workflows/ci.yml            # 3-stage CI (lint+test → frontend → docker)
└── .env.example                         # Template for API keys + config
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
# Edit .env with your API keys (GOOGLE_API_KEY and ANTHROPIC_API_KEY are required)
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

## Configuration

### Tier 1: Infrastructure (`.env`)

Environment variables loaded via pydantic-settings:

```env
# Required API Keys
GOOGLE_API_KEY=...              # Gemini API (parsing, embeddings)
ANTHROPIC_API_KEY=...           # Claude API (scoring, cover letters, agent)

# Optional API Keys
JSEARCH_API_KEY=...             # RapidAPI JSearch (paid scraper source)
ADZUNA_APP_ID=...               # Adzuna job board
ADZUNA_APP_KEY=...

# Database & Queue
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/job_agent
REDIS_URL=redis://localhost:6379/0

# Model Configuration (defaults shown)
GEMINI_MODEL=gemini-3.1-pro-preview
CLAUDE_MODEL=claude-sonnet-4-6
EMBEDDING_MODEL=gemini-embedding-001

# Claude Proxy (optional — routes Claude calls through a local proxy like claude-code-proxy)
# ANTHROPIC_BASE_URL=http://localhost:42069

# Observability (optional)
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=job-application-agent
```

### Tier 2: User Preferences (`backend/data/user_config.yaml`)

Pydantic-validated preferences controlling job search, matching weights, and scraper config:

```yaml
# Job search targets
job_titles:
  - Software Engineer
  - AI Engineer
  - Full-stack Developer
locations:
  - Remote
  - United States
  - Canada
salary_min: 100000
salary_max: 200000
workplace_types:
  - remote
  - hybrid
experience_level: mid          # entry | mid | senior | lead | executive

# Scoring weights (must sum to 1.0)
weights:
  skills: 0.35
  experience: 0.25
  education: 0.15
  location: 0.15
  salary: 0.10

# Search settings
employment_types:
  - FULLTIME                   # FULLTIME | PARTTIME | CONTRACT | INTERNSHIP | TEMPORARY
date_posted: month             # today | 3days | week | month | all
final_results_count: 10
num_pages_per_source: 5

# Scraper sources
enabled_sources:
  - jsearch
  - greenhouse
  - lever
  - arbeitnow

# ATS-specific boards
greenhouse_board_tokens:
  - stripe
  - cloudflare
  - figma
  - airbnb
lever_companies:
  - netflix
workday_urls: []
```

## API Endpoints

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs` | List jobs (paginated, filterable by location/source/search) |
| `GET` | `/api/jobs/{id}` | Get job details with full description |
| `POST` | `/api/jobs/scrape` | Trigger background scraping (rate-limited 10/min) |
| `GET` | `/api/jobs/scrape/{task_id}/status` | Poll scraping task progress |

### Matches

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/matches` | List scored matches (sorted by score descending) |
| `GET` | `/api/matches/{id}` | Match detail with breakdown, strengths, gaps |
| `POST` | `/api/matches/run` | Trigger matching pipeline background task |
| `POST` | `/api/matches/{id}/rescore` | Re-run scoring for a specific match |

### Agent

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agent/start` | Start browser agent for a job (rate-limited 10/min) |
| `POST` | `/api/agent/resume/{thread_id}` | Resume interrupted agent (approve/reject/edit) |
| `WS` | `/ws/agent-status` | Real-time agent progress via WebSocket |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/reports/generate` | Generate PDF/HTML report for a match |
| `GET` | `/api/reports/{id}/download` | Download generated report |
| `POST` | `/api/reports/cover-letter` | Generate personalized cover letter |

### Config

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/config/preferences` | Load current user preferences |
| `PUT` | `/api/config/preferences` | Update preferences (validates weight sum) |
| `POST` | `/api/config/resume` | Upload resume (multipart file) |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (used by Docker HEALTHCHECK) |

## Browser Agent

The LangGraph-based browser agent handles job application form filling with human-in-the-loop approval:

```
START → detect_ats → [route]
  ├─ Greenhouse/Lever → api_submit → END (direct API, no browser needed)
  └─ Workday/Generic → navigate → fill_fields → upload_resume → answer_questions
                         → review_node (INTERRUPT: human approval)
                           ├─ approve → submit → END
                           ├─ reject  → abort  → END
                           └─ edit    → fill_fields (loop back)
```

The agent pauses at `review_node` using LangGraph's `interrupt()`, saves state, and shows the filled fields plus screenshot in the dashboard for human review before submission. Progress updates stream in real-time via WebSocket.

### ATS Strategies

| ATS Platform | Strategy | Method |
|---|---|---|
| Greenhouse | Direct API | POST to Greenhouse Application API |
| Lever | Direct API | POST to Lever Application API |
| Workday | Browser automation | Playwright fills Workday forms |
| Generic | Browser automation | Playwright with field detection heuristics |

## MCP Server

The project includes a [Model Context Protocol](https://modelcontextprotocol.io/) server for integration with Claude Desktop, Cursor, or other MCP clients.

### Tools

| Tool | Description |
|------|-------------|
| `search_jobs` | Search job postings with location/query filters |
| `match_resume_to_jobs` | Scrape + score jobs against current resume |
| `fill_application` | Preview or submit job application (dry_run default) |
| `generate_cover_letter` | Generate personalized cover letter |
| `generate_report` | Generate HTML match report |
| `get_preferences` | Load user configuration |
| `update_preferences` | Update job search preferences |

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

## Background Worker

ARQ (async Redis queue) handles long-running tasks so the API responds immediately:

| Task | Trigger | Description |
|------|---------|-------------|
| `run_scraping` | `POST /api/jobs/scrape` | Execute all enabled scrapers, deduplicate, index into ChromaDB |
| `run_matching` | `POST /api/matches/run` | Pre-filter → embed → retrieve → quick-score → full-score |
| `run_agent` | `POST /api/agent/start` | Start LangGraph browser agent workflow |

Poll `GET /api/jobs/scrape/{task_id}/status` for progress, or connect to WebSocket for real-time updates.

## Database Schema

6 tables managed by SQLAlchemy 2.0 async ORM with Alembic migrations:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | User profile | resume_text, email, name |
| `jobs` | Normalized job postings | title, company, source, external_id (unique pair), description, salary, location |
| `match_results` | Scoring results | user_id → jobs FK, overall_score, breakdown (JSON), reasoning, strengths, missing_skills |
| `applications` | Submitted applications | match_id FK, status (pending/submitted/rejected), submitted_at |
| `cover_letters` | Generated cover letters | match_id FK, content, model_used |
| `agent_logs` | Browser agent step logs | thread_id, step, action, screenshot_path, timestamp |

## Testing

### Test Summary

| Suite | Tests | Description |
|-------|------:|-------------|
| Matching (Phase 1) | 73 | Pre-filter, embedder, retriever, scorer (full + quick), pipeline, LLM factory |
| Scraping (Phase 2) | 56 | JSearch, Greenhouse, Lever, Adzuna, Arbeitnow, normalizer, dedup, orchestrator |
| DB & API (Phase 3) | 47 | Models, routers (jobs/matches/agent/config), WebSocket, ARQ tasks |
| Agent (Phase 4) | 71 | State, graph routing, field mapper, ATS strategies, interrupt/resume |
| Reports (Phase 6) | 52 | PDF generator, cover letter, templates, evaluation metrics |
| MCP (Phase 7) | 22 | Tools, resources, prompts |
| Docker (Phase 7) | 21 | Compose validation, image builds |
| Config | 16 | Settings, UserConfig, MatchingWeights validation |
| Integration | 31 | Full user workflow (9-step), E2E scraping/matching |
| Frontend | 36 | Components, stores (Vitest + React Testing Library + MSW) |
| **Total** | **~425** | |

### Running Tests

```bash
# All backend unit tests (excludes integration + docker tests)
cd backend
uv run pytest -m "not integration and not docker" -q

# Full backend suite
uv run pytest -v

# Specific modules
uv run pytest tests/test_matching/ -v        # Matching pipeline
uv run pytest tests/test_scraping/ -v        # Scrapers
uv run pytest tests/test_agent/ -v           # Browser agent
uv run pytest tests/test_reports/ -v         # Reports + cover letters
uv run pytest tests/test_mcp/ -v             # MCP server
uv run pytest tests/test_api/ -v             # API routers
uv run pytest tests/test_config/ -v          # Configuration

# User workflow integration test (9-step end-to-end)
uv run pytest tests/test_integration/test_user_workflow.py -v

# E2E pipeline test (requires running Claude proxy + Google API key)
cd backend && python tests/e2e_pipeline_test.py

# Frontend
cd frontend
npx vitest run
```

### User Workflow Integration Test

`test_user_workflow.py` simulates the complete user journey with mocked external APIs but real internal code paths:

1. **Resume & Config** — Upload resume, configure preferences
2. **Job Scraping** — Orchestrate scrapers, deduplicate across sources
3. **Job Storage** — Store in DB, verify API retrieval with pagination + filters
4. **Matching** — Pre-filter → retrieve → quick-score → full-score, verify sorted results
5. **Reports** — Generate HTML reports (high/low scores), cover letters
6. **Evaluation** — F1 skill matching, score accuracy metrics
7. **Browser Agent** — Full LangGraph cycle: detect ATS → fill → interrupt → approve/reject
8. **MCP Server** — Tools, resources, dry-run application
9. **Docker** — Compose validation, CI workflow

### E2E Pipeline Test

`e2e_pipeline_test.py` runs the full pipeline against live APIs (Arbeitnow, Greenhouse, Lever) for 3 search titles (Software Engineer, AI Engineer, Full-stack Developer). Requires a running Claude proxy at `localhost:42069` and a valid Google API key. Outputs a detailed Markdown report and JSON data file with all scored matches.

## Docker Deployment

### Services

| Service | Image | Purpose | Port |
|---------|-------|---------|------|
| `db` | postgres:16-alpine | PostgreSQL database | 5432 |
| `redis` | redis:7-alpine | ARQ task queue | 6379 |
| `backend` | Built from ./backend | FastAPI + ChromaDB | 8000 |
| `worker` | Built from ./backend | ARQ background worker | — |
| `frontend` | Built from ./frontend | React (Nginx) | 3000 |

### Volumes

- `postgres_data` — PostgreSQL data persistence
- `redis_data` — Redis persistence
- `chroma_data` — ChromaDB vector store persistence
- `./backend/data` — Mounted for user config and resume files

## CI/CD

GitHub Actions runs a 3-stage pipeline on every push:

1. **Backend** — Lint with ruff, type-check with mypy, run unit tests
2. **Frontend** — Install dependencies, run Vitest
3. **Docker** (depends on both) — Validate docker-compose.yml, build all images

## Tech Stack

### Backend
- **Python 3.13** with **uv** package manager and **hatchling** build system
- **FastAPI** + uvicorn (async web framework)
- **SQLAlchemy 2.0** + asyncpg/aiosqlite (async ORM with Alembic migrations)
- **LangChain** + **LangGraph** (AI orchestration + agent state machine)
- **ChromaDB** (vector store) + **FlashRank** (cross-encoder reranking)
- **ARQ** (async Redis task queue)
- **Jinja2** + **WeasyPrint** (HTML/PDF report generation)
- **Playwright** + **browser-use** (browser automation)
- **FastMCP** (Model Context Protocol server)
- **SlowAPI** (rate limiting)
- **pydantic-settings** (configuration management)

### Frontend
- **React 19** + **TypeScript 5.9** + **Vite 7**
- **Zustand 5** (UI state) + **TanStack Query v5** (server state + caching)
- **Recharts 3** (radar charts for score visualization)
- **react-use-websocket** (real-time agent updates)
- **Tailwind CSS 4** (styling)
- **React Router v7** (routing)
- **Vitest 4** + **React Testing Library** + **MSW** (testing)

### Infrastructure
- **PostgreSQL 16** (primary database)
- **Redis 7** (task queue backend)
- **Docker Compose** (5-service deployment)
- **Nginx** (frontend reverse proxy in production)
- **GitHub Actions** (CI/CD pipeline)

## License

MIT
