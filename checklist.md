# Implementation Checklist: Design.md vs Actual Code

> Auto-generated on 2026-02-25 by comparing `Design.md` with actual project source files.
> Legend: [x] Done | [~] Partial/Scaffolded | [ ] Not implemented

---

## 1. Job Scraping and Search Module (Design.md Section 1)

### Browser Automation
- [~] Playwright integration — used in `WorkdayScraper` only; no standalone Playwright toolkit
- [ ] **patchright** stealth patching — not installed or used anywhere
- [ ] Residential proxy rotation (Bright Data / SmartProxy)

### Tier 1 — Direct ATS APIs
- [x] Greenhouse Job Board API scraper (`app/services/scraping/api/greenhouse.py`)
- [x] Lever Postings API scraper (`app/services/scraping/api/lever.py`)
- [ ] Greenhouse programmatic application submission via `POST`
- [ ] Lever application submission via `POST`

### Tier 2 — Aggregator APIs
- [x] JSearch (RapidAPI) scraper (`app/services/scraping/api/jsearch.py`)
- [ ] **Adzuna API** scraper — not implemented
- [ ] **Arbeitnow API** scraper — not implemented

### Tier 3 — Browser Automation Scrapers
- [x] Workday XHR interception scraper (`app/services/scraping/browser/workday.py`)
- [x] Generic JSON-LD extraction scraper (`app/services/scraping/browser/generic.py`)
- [x] LinkedIn excluded per ToS (correctly not scraped)

### Data Pipeline
- [x] Normalized `JobPosting` Pydantic schema (`app/schemas/matching.py`)
- [x] Deduplication by composite key (`app/services/scraping/deduplicator.py`)
- [x] Multi-scraper orchestrator (`app/services/scraping/orchestrator.py`)
- [x] JSON-LD `@type: "JobPosting"` parser in generic scraper
- [x] Normalizer (`app/services/scraping/normalizer.py`)
- [x] Test fixtures for all scrapers (`tests/fixtures/scraping/`)

### Testing
- [x] Greenhouse scraper tests
- [x] Lever scraper tests
- [x] JSearch scraper tests
- [x] Normalizer tests
- [x] Deduplicator tests
- [x] JSON-LD parser tests
- [x] Orchestrator tests

---

## 2. AI Matching Engine (Design.md Section 2)

### Two-Stage Retrieval + Reranking
- [x] Stage 1: Vector similarity retrieval via ChromaDB (`app/services/matching/retriever.py`)
- [x] Stage 2: FlashRank cross-encoder reranking (`TwoStageRetriever`)
- [x] `ContextualCompressionRetriever` pattern

### Embedding Model
- [~] Design specifies **OpenAI text-embedding-3-small**; actual uses **Gemini embedding-001** — functional equivalent, different provider
- [x] Embeddings via `langchain-google-genai` (`GoogleGenerativeAIEmbeddings`)

### Vector Database
- [x] ChromaDB for development (`app/services/matching/embedder.py`)
- [ ] Qdrant upgrade path for production — not configured

### LLM-as-Judge Scoring
- [x] `JobMatchScore` structured output with Pydantic validation (`app/schemas/matching.py`)
- [x] `with_structured_output()` pattern (`app/services/matching/scorer.py`)
- [x] Score breakdown: skills, experience, education, location, salary
- [x] Missing skills + strengths + reasoning fields
- [x] Interview talking points field

### Pipeline Orchestrator
- [x] Full pipeline: embed → retrieve → rerank → score (`app/services/matching/pipeline.py`)
- [x] User config integration (locations, salary preferences, weights)

### Testing
- [x] Embedder tests
- [x] Retriever tests
- [x] Scorer tests
- [x] Pipeline tests
- [x] LLM factory tests

---

## 3. Auto-Fill Agent (Design.md Section 3)

### browser-use Integration
- [ ] **browser-use library** — NOT installed in `pyproject.toml`, NOT used in code
- [ ] DOM restructuring + element labeling via browser-use
- [ ] Screenshot analysis feedback loop
- [ ] Custom `@controller.action` for file uploads

### LangGraph Orchestration
- [x] `StateGraph` with full workflow (`app/services/agent/graph.py`)
- [x] Nodes: detect_ats → navigate → fill → upload → answer → review → submit/abort
- [x] Conditional routing: ATS detection, review decision
- [x] `interrupt()` for human-in-the-loop review (`app/services/agent/nodes.py:review_node`)
- [x] `compile_agent_graph()` with optional checkpointer
- [ ] Actual browser execution in nodes — all have `TODO: Use browser-use` placeholders
- [ ] Screenshot capture during form filling

### ATS Form Handling
- [x] ATS platform detection by URL pattern (Greenhouse, Lever, Workday)
- [x] Field mapper for profile → form field mapping (`app/services/agent/field_mapper.py`)
- [x] Greenhouse ATS strategy file (`app/services/agent/ats/greenhouse.py`)
- [x] Lever ATS strategy file (`app/services/agent/ats/lever.py`)
- [ ] Actual Greenhouse API submission — `api_submit` is a TODO placeholder
- [ ] Actual Lever API submission — same
- [ ] Workday multi-page wizard handling
- [ ] Custom screening question answering via LLM — placeholder only
- [ ] File upload via `set_input_files()` / `expect_file_chooser()`

### Testing
- [x] State management tests
- [x] Field mapper tests
- [x] Node function tests
- [x] Graph structure tests
- [x] ATS Greenhouse strategy tests
- [x] Interrupt/human-in-the-loop tests

---

## 4. Report Generation (Design.md Section 4)

### WeasyPrint + Jinja2 Reports
- [x] `ReportGenerator` class (`app/services/reports/generator.py`)
- [x] Jinja2 HTML template (`app/services/reports/templates/report.html`)
- [x] `generate_pdf()` with WeasyPrint (optional, graceful fallback to HTML)
- [x] Score color coding: green (>=8), yellow (>=6), red (<6)
- [x] Report sections: cover page, score breakdown, reasoning, strengths, skill gaps
- [x] Interview talking points section
- [x] Salary range section
- [x] Cover letter section in report
- [ ] **WeasyPrint** not in `pyproject.toml` dependencies — only available in Docker image
- [ ] Company overview section — not in template
- [ ] Salary market analysis — not in template
- [ ] Learning recommendations for missing skills — not in template

### Cover Letter Generation
- [x] LCEL chain: prompt → Claude → StrOutputParser (`app/services/reports/cover_letter.py`)
- [x] Temperature 0.7 for creative writing
- [x] Prompt references strengths, missing skills, resume, job description
- [x] `CoverLetterGenerator` async class

### API Integration
- [~] Report generation endpoint (`/api/reports/generate`) — returns `queued` status but PDF generation is TODO
- [~] Cover letter endpoint (`/api/reports/cover-letter`) — saves placeholder, doesn't call `CoverLetterGenerator`
- [~] Report download endpoint (`/api/reports/{id}/download`) — returns 404 always (TODO)

### Testing
- [x] Generator tests
- [x] Cover letter tests
- [x] Template rendering tests
- [x] Evaluation function tests

---

## 5. React Dashboard (Design.md Section 5)

### Technology Stack
- [x] Vite 7.3+ bundler
- [x] React 19.2+ with TypeScript 5.9
- [x] Tailwind CSS 4.2
- [ ] **shadcn/ui** components — NOT installed, using custom CSS instead
- [ ] Radix UI primitives — NOT installed

### State Management
- [x] Zustand 5.0 for client/UI state (`stores/app-store.ts`, `stores/agent-store.ts`)
- [x] TanStack Query 5.90 for server state (`hooks/use-jobs.ts`, `hooks/use-matches.ts`)

### Components
- [x] `JobCard` — job listing card
- [x] `JobList` — job list container
- [x] `JobFilters` — search/filter controls
- [x] `MatchDetail` — match detail view
- [x] `PreferencesForm` — user preferences editor
- [x] `ReviewDialog` — human-in-the-loop review modal
- [x] `AgentProgress` — agent execution progress tracker
- [x] `ScoreRadarChart` — Recharts radar visualization
- [x] `SkillGapAnalysis` — skill gap visualization

### Pages
- [x] `DashboardPage` — main dashboard with job matches
- [x] `SettingsPage` — settings/preferences page
- [x] `NavBar` with routing

### Integrations
- [x] React Router 7.13 for page navigation
- [x] WebSocket hook for real-time agent updates (`hooks/use-agent-ws.ts`)
- [x] `react-use-websocket` 4.13
- [x] Recharts 3.7 for visualization
- [ ] **Orval** type-safe API client generation — NOT used (manual API client)
- [ ] `<Activity />` component from React 19 — not used

### Testing
- [x] JobCard component test
- [x] PreferencesForm component test
- [x] ReviewDialog component test
- [x] ScoreRadarChart component test
- [x] SkillGapAnalysis component test
- [x] App store (Zustand) tests
- [x] Agent store tests
- [x] MSW mock server setup

---

## 6. Observability and Evaluation (Design.md Section 6)

### LangSmith
- [x] LangSmith configuration fields in Settings (`langsmith_tracing`, `langsmith_api_key`, `langsmith_project`)
- [ ] LangSmith tracing actually enabled and verified working
- [ ] LangSmith experiments with custom evaluators running against a dataset

### Evaluation Functions
- [x] `skill_match_f1` evaluator (`app/services/reports/evaluation.py`)
- [x] `score_accuracy` evaluator
- [ ] **RAGAS** evaluation for RAG retrieval quality — not installed, not implemented
- [ ] Hand-labeled dataset of 50-100 resume-job pairs
- [ ] Custom NDCG ranking metrics

---

## 7. MCP Integration (Design.md Section 7)

### FastMCP Server
- [x] FastMCP 3.0+ server (`app/mcp/server.py`)
- [x] `__main__.py` entry point for `uv run python -m app.mcp`

### Tools
- [x] `search_jobs` — scrape and return job listings
- [x] `match_resume_to_jobs` — full pipeline scrape → match → score
- [x] `fill_application` — preview/dry-run application fill
- [x] `generate_cover_letter` — Claude-powered cover letter
- [x] `generate_report` — HTML match report generation
- [ ] `submit_application` as separate destructive tool — combined into `fill_application`

### Resources
- [x] `resume://current` — loads current resume text
- [x] `preferences://job-search` — returns user config as JSON

### Prompts
- [x] `cover_letter_prompt` — guided cover letter writing prompt

### Transport
- [x] stdio transport for local use (Claude Desktop / Cursor)
- [~] Streamable HTTP — supported by FastMCP but not explicitly configured with `--transport` flag

### Testing
- [x] MCP tools tests
- [x] MCP resources tests
- [x] MCP prompts tests

---

## 8. Multi-LLM Support (Design.md Section 8)

### Model Routing
- [x] `LLMTask` enum with task categories (`app/services/llm_factory.py`)
- [x] Gemini Flash for cheap tasks (PARSE, EXTRACT, CLASSIFY)
- [x] Claude Sonnet for reasoning tasks (SCORE, COVER_LETTER, BROWSER_AGENT)
- [x] Task-based routing via `get_llm(task)` factory

### Provider Support
- [x] `langchain-google-genai` (Gemini) integration
- [x] `langchain-anthropic` (Claude) integration
- [ ] **Ollama** / `langchain-ollama` for local/offline use — not installed
- [ ] **LiteLLM** proxy — correctly excluded per design

### Cost Optimization
- [ ] `InMemoryCache` or `SQLiteCache` for LangChain — not implemented
- [ ] `.batch()` for bulk embedding operations — not used

---

## 9. Configuration (Design.md Section 9)

### Tier 1: Infrastructure Config
- [x] `pydantic-settings` with `.env` support (`app/config.py`)
- [x] `SecretStr` for API keys (google, anthropic, jsearch, langsmith)
- [x] Database URL, Redis URL configuration
- [x] Model name configuration (gemini, claude, embedding)
- [x] Path configuration (data_dir, chroma_db_dir, user_config_path)
- [x] Singleton caching via `get_settings()`

### Tier 2: User Preferences (YAML)
- [x] YAML config file loading (`load_user_config()`)
- [x] `UserConfig` Pydantic model with validation
- [x] `MatchingWeights` with sum-to-1.0 validation
- [x] Job titles, locations, salary range, workplace types
- [x] Experience level validation (entry/mid/senior/lead/executive)
- [x] Resume path configuration
- [x] `data/user_config.yaml` file exists

---

## 10. Docker and Deployment (Design.md Section 10)

### Backend Dockerfile
- [x] Multi-stage build with uv (`backend/Dockerfile`)
- [x] `api` target for FastAPI server
- [x] `worker` target for ARQ background worker
- [x] WeasyPrint system dependencies installed
- [x] Health check configured
- [ ] Non-root user (`appuser`) — not set up in Dockerfile

### Frontend Dockerfile
- [x] Node.js 22 build stage (`frontend/Dockerfile`)
- [x] Nginx production stage
- [x] Custom `nginx.conf`
- [x] Health check configured

### Docker Compose
- [x] PostgreSQL 16-alpine with health check
- [x] Redis 7-alpine with health check
- [x] Backend (FastAPI) with env config
- [x] Worker (ARQ) with env config
- [x] Frontend (Nginx)
- [x] Named volumes: postgres_data, redis_data, chroma_data
- [ ] **Qdrant** service — NOT in docker-compose (design mentions it for production)

### CI/CD
- [x] GitHub Actions workflow (`.github/workflows/ci.yml`)
- [x] Backend: lint (ruff) + type check (mypy) + unit tests (pytest)
- [x] Frontend: test (vitest)
- [x] Docker: validate compose + build all images
- [x] `astral-sh/setup-uv@v5` for uv installation
- [ ] Deployment to Railway or Hetzner — not configured
- [ ] Auto-deploy on push to main — not configured

---

## 11. PostgreSQL Database (Design.md Section 11)

### SQLAlchemy Models (6 Core Tables)
- [x] `User` model (`app/models/user.py`)
- [x] `Job` model (`app/models/job.py`)
- [x] `MatchResult` model (`app/models/match.py`)
- [x] `Application` model (`app/models/application.py`)
- [x] `CoverLetter` model (`app/models/cover_letter.py`)
- [x] `AgentLog` model (`app/models/agent_log.py`)
- [x] `Base` declarative base (`app/models/base.py`)

### Database Infrastructure
- [x] Async session factory (`app/db/session.py`)
- [x] Alembic configured (`alembic.ini`, `alembic/env.py`)
- [ ] Alembic migration files — `alembic/versions/` is **empty** (no migrations generated)
- [ ] GIN index on `tsvector` for full-text search — not verified (no migrations)
- [ ] Composite unique index on `(external_id, source)` — not verified
- [ ] Covering index on `(user_id, overall_score DESC)` — not verified

### Testing
- [x] Database model tests with aiosqlite in-memory
- [x] Test conftest with session fixtures

---

## 12. FastAPI Backend Architecture (Design.md Section 12)

### Application Structure
- [x] `main.py` with middleware and router mounting
- [x] `config.py` with Pydantic Settings
- [x] `dependencies.py` for dependency injection
- [x] Health check endpoint (`/health`)

### Routers
- [x] `/api/jobs/*` — job CRUD
- [x] `/api/matches/*` — match queries
- [x] `/api/agent/*` — agent start/resume + WebSocket
- [x] `/api/reports/*` — report generation + cover letters
- [x] `/api/config/*` — preferences read/update + resume upload

### Middleware
- [x] CORS for Vite dev server (`:5173`) and production (`:3000`)
- [ ] Request logging with duration timing — not implemented
- [ ] Global exception handler returning structured JSON errors — not implemented
- [ ] Rate limiting via SlowAPI — not installed or configured

### Background Tasks (ARQ)
- [x] ARQ worker settings (`app/worker/settings.py`)
- [x] `run_scraping` task — functional
- [~] `run_matching` task — placeholder with TODO
- [~] `run_agent` task — placeholder with TODO
- [x] Worker startup/shutdown hooks

### WebSocket
- [x] `ConnectionManager` pattern (`app/core/websocket.py`)
- [x] `/ws/agent-status` endpoint (`app/routers/agent.py`)
- [x] Broadcast to connected clients
- [x] Frontend `useAgentWebSocket` hook

### Testing
- [x] Jobs router tests
- [x] Matches router tests
- [x] Agent router tests
- [x] Config router tests
- [x] WebSocket tests
- [x] ARQ worker task tests
- [x] Integration / E2E tests

---

## Summary

| Section | Done | Partial | Not Done | Total |
|---------|------|---------|----------|-------|
| 1. Scraping | 14 | 1 | 4 | 19 |
| 2. Matching | 12 | 1 | 1 | 14 |
| 3. Auto-Fill Agent | 12 | 0 | 8 | 20 |
| 4. Reports | 10 | 3 | 3 | 16 |
| 5. Dashboard | 20 | 0 | 3 | 23 |
| 6. Observability | 3 | 0 | 4 | 7 |
| 7. MCP | 11 | 1 | 1 | 13 |
| 8. Multi-LLM | 5 | 0 | 3 | 8 |
| 9. Configuration | 11 | 0 | 0 | 11 |
| 10. Docker | 12 | 0 | 3 | 15 |
| 11. Database | 9 | 0 | 4 | 13 |
| 12. FastAPI | 15 | 2 | 3 | 20 |
| **TOTAL** | **134** | **8** | **37** | **179** |

**Overall completion: ~77% (134 done + 8 partial out of 179 items)**

---

## Critical Gaps (High Priority)

1. **browser-use not installed/integrated** — The centerpiece of the auto-fill agent (Design Section 3) is completely missing. All agent nodes have `TODO` placeholders.
2. **Alembic migrations not generated** — Database schema exists as models but no migration files have been created. The app cannot create tables on a real PostgreSQL instance.
3. **Report API endpoints are placeholders** — The `reports` router returns stubs; PDF generation and cover letter generation are not wired to the actual service classes.
4. **ARQ background tasks incomplete** — `run_matching` and `run_agent` are TODO stubs.

## Medium Priority Gaps

5. **WeasyPrint not in pyproject.toml** — Only available in Docker image; local PDF generation will silently fall back to HTML bytes.
6. **shadcn/ui not used** — Dashboard uses plain CSS instead of the designed component library.
7. **Adzuna and Arbeitnow scrapers** — Two of three Tier 2 aggregator APIs are missing.
8. **Observability** — LangSmith config exists but no evaluation pipeline, no RAGAS, no labeled datasets.
9. **Ollama local model support** — Not installed.
10. **Request logging, error handling middleware, rate limiting** — Not implemented.
