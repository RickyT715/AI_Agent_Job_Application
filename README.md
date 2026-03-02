# AI Job Application Agent

An end-to-end AI-powered system that scrapes job boards, matches postings against your resume using a multi-stage pipeline, generates cover letters and reports, and auto-fills applications with human-in-the-loop approval. Supports both **English** and **Chinese** job markets.

Uses **Gemini 3.1 Pro** for cheap tasks (parsing, extraction) and **Claude Sonnet 4.6** for reasoning tasks (scoring, cover letters, browser agent). Embeddings via **Gemini embedding-001**. Matching pipeline includes heuristic pre-filtering, vector retrieval, cross-encoder reranking, LLM quick-scoring, and full multi-dimensional LLM-as-Judge evaluation.

## Architecture

```
Resume Upload ──► Scrape Jobs ──► Pre-Filter ──► Match & Score ──► Reports ──► Auto-Fill
                      │               │               │               │            │
             English Pipeline:    Seniority/       ChromaDB +      Jinja2 HTML   LangGraph
               JSearch API       Location/Type    FlashRank +     + Claude       agent with
               Greenhouse        heuristics       Quick-Score +   cover letters  interrupt()
               Lever                              Claude Full                    for human
               Adzuna                             LLM-as-Judge                   review
               Arbeitnow
               RemoteOK
               WeWorkRemotely
                      │
             Chinese Pipeline (中文):
               Tencent (腾讯)
               NetEase (网易)          Auto-detect     jieba ATS +
               MokaHR                 language →     FlashRank
               Alibaba (阿里)                        multilingual /
               JD Campus (京东)                      BGE reranker
               BOSS直聘 (browser)
               Zhaopin (browser)
               51job (browser)
               Lagou (browser)
               ByteDance (字节)
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
3. **Cross-encoder reranking** — FlashRank narrows to top-10 (local CPU, free). For Chinese resumes, auto-selects FlashRank multilingual or BGE reranker.
4. **Quick-score** — Claude rates relevance 1-10 with a lightweight prompt (500-char job brief, JSON response). Jobs below threshold 4 are skipped.
5. **Full LLM-as-Judge scoring** — Claude scores surviving candidates on skills/experience/education/location/salary (1-10 each) with explicit weight percentages from `MatchingWeights` config. Returns structured output with reasoning, strengths, missing skills, and interview talking points.

**Chinese pipeline auto-detection:** When the resume is in Chinese, `ats_mode=auto` selects jieba-based ATS keyword scoring (vs regex for English), and `reranker_mode=auto` selects BGE reranker (vs FlashRank for English).

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
│   │   │   │   ├── retriever.py         # Vector search + FlashRank/BGE rerank
│   │   │   │   ├── scorer.py            # LLM-as-Judge (full + quick score)
│   │   │   │   ├── ats_scorer.py        # ATS keyword scoring (regex + jieba)
│   │   │   │   └── pipeline.py          # 5-stage orchestrator
│   │   │   ├── scraping/
│   │   │   │   ├── base.py              # Abstract BaseScraper interface
│   │   │   │   ├── orchestrator.py      # Multi-source coordination + dedup
│   │   │   │   ├── normalizer.py        # Raw data → JobPosting schema
│   │   │   │   ├── deduplicator.py      # Cross-source duplicate removal
│   │   │   │   ├── api/                 # API-based scrapers
│   │   │   │   │   ├── jsearch.py       # RapidAPI JSearch (requires API key)
│   │   │   │   │   ├── greenhouse.py    # Greenhouse boards (requires board tokens)
│   │   │   │   │   ├── lever.py         # Lever postings (requires company slugs)
│   │   │   │   │   ├── adzuna.py        # Adzuna (requires app ID + key)
│   │   │   │   │   ├── arbeitnow.py     # Arbeitnow (public, no auth)
│   │   │   │   │   ├── remoteok.py      # RemoteOK (public, no auth)
│   │   │   │   │   ├── weworkremotely.py# WeWorkRemotely (public, no auth)
│   │   │   │   │   ├── tencent.py       # Tencent Careers (public, no auth)
│   │   │   │   │   ├── netease.py       # NetEase Careers (public, no auth)
│   │   │   │   │   ├── mokahrjob.py     # MokaHR (requires org IDs)
│   │   │   │   │   ├── alibaba.py       # Alibaba (requires app key)
│   │   │   │   │   ├── jd_campus.py     # JD Campus (public, no auth)
│   │   │   │   │   ├── bytedance.py     # ByteDance (public, no auth)
│   │   │   │   │   ├── zhaopin.py       # Zhaopin (session-based, fragile)
│   │   │   │   │   ├── job51.py         # 51job (font obfuscation, fragile)
│   │   │   │   │   ├── lagou.py         # Lagou (anti-scraping, fragile)
│   │   │   │   │   └── boss_zhipin.py   # BOSS直聘 (requires cookie)
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
│   ├── tests/                           # 625 backend + 36 frontend tests
│   │   ├── test_matching/               # Pipeline, pre-filter, scorer, embedder, retriever, ATS
│   │   ├── test_scraping/               # All 18 scrapers, dedup, normalizer, orchestrator
│   │   ├── test_agent/                  # Graph, nodes, ATS handlers, interrupts
│   │   ├── test_api/                    # All routers + WebSocket
│   │   ├── test_db/                     # Model CRUD + constraints
│   │   ├── test_reports/                # PDF, cover letter, evaluation
│   │   ├── test_mcp/                    # Tools, resources, prompts
│   │   ├── test_worker/                 # ARQ task tests
│   │   ├── test_docker/                 # Compose validation
│   │   ├── test_config/                 # Settings + UserConfig validation
│   │   ├── test_integration/            # Full user workflow (9-step)
│   │   └── e2e_pipeline_test.py         # Live E2E test (English + Chinese pipelines)
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

---

## Setup Guide

### Prerequisites

| Tool | Version | Required for |
|------|---------|--------------|
| Python | 3.13+ | Backend |
| [uv](https://docs.astral.sh/uv/) | latest | Python package manager |
| Node.js | 22+ | Frontend |
| Docker & Docker Compose | latest | Full deployment (or run Postgres/Redis manually) |

### Step 1: Clone and Configure Environment

```bash
git clone <repo-url>
cd AI_Agent_Job_Application
cp .env.example .env
```

Edit `.env` and fill in your API keys. See the [API Keys](#api-keys-env) section below for what each key does and where to get it.

### Step 2: Backend Setup

```bash
cd backend
uv sync --dev
```

This installs all Python dependencies including jieba (Chinese NLP), FlagEmbedding (BGE reranker), Playwright, etc.

**Install Playwright browsers** (required for browser-based scrapers and the application agent):

```bash
uv run playwright install chromium
```

### Step 3: Database Setup

**Option A: Docker (recommended)**
```bash
# From project root — starts just Postgres + Redis
docker compose up -d db redis
```

**Option B: Local install**
- Install PostgreSQL 16 and create a database named `job_agent` with user `postgres`/`postgres`
- Install Redis 7 on default port 6379

**Run migrations:**
```bash
cd backend
uv run alembic upgrade head
```

### Step 4: Frontend Setup

```bash
cd frontend
npm install
```

### Step 5: Run the App (Development)

```bash
# Terminal 1: Backend API
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend dev server
cd frontend
npm run dev
```

Open http://localhost:5173 for the dashboard. API docs at http://localhost:8000/docs.

### Step 6: Run with Docker (Full Stack)

```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### Step 7: Run Tests

```bash
# Backend unit tests (625 tests, no external APIs needed)
cd backend
uv run pytest --ignore=tests/e2e_pipeline_test.py --ignore=tests/test_integration/ -q

# Frontend tests (36 tests)
cd frontend
npx vitest run
```

---

## Configuration

### API Keys (`.env`)

The table below shows every API key, whether it's required, where to get it, and what breaks without it.

| Env Variable | Required? | Where to Get It | What It Enables |
|---|---|---|---|
| `GOOGLE_API_KEY` | **Yes** | [Google AI Studio](https://aistudio.google.com/apikey) | Gemini LLM (parsing, extraction) + embedding generation. **Nothing works without this.** |
| `ANTHROPIC_API_KEY` | **Yes** (or use proxy) | [Anthropic Console](https://console.anthropic.com/) | Claude scoring, cover letters, browser agent. Set `ANTHROPIC_BASE_URL` instead if using a local proxy. |
| `JSEARCH_API_KEY` | Optional | [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) | JSearch scraper (aggregates LinkedIn, Indeed, Glassdoor). Free tier: 100 requests/month. |
| `ADZUNA_APP_ID` | Optional | [Adzuna Developer](https://developer.adzuna.com/) | Adzuna job board scraper. Free tier available. |
| `ADZUNA_APP_KEY` | Optional | Same as above | Used together with `ADZUNA_APP_ID`. |
| `LANGSMITH_API_KEY` | Optional | [LangSmith](https://smith.langchain.com/) | LLM call tracing and debugging. Not needed for normal use. |

**Using a Claude proxy** (e.g., [claude-code-proxy](https://github.com/nicobailon/claude-code-proxy)):

```env
ANTHROPIC_BASE_URL=http://localhost:42069
ANTHROPIC_API_KEY=proxy-no-key-needed
```

### Full `.env` Reference

```env
# ── Required ──────────────────────────────────────────────────────────
GOOGLE_API_KEY=your-google-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# ── Database & Queue (defaults match docker-compose) ──────────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/job_agent
REDIS_URL=redis://localhost:6379/0

# ── Optional API Keys ─────────────────────────────────────────────────
JSEARCH_API_KEY=your-rapidapi-key-here
ADZUNA_APP_ID=your-adzuna-app-id
ADZUNA_APP_KEY=your-adzuna-app-key

# ── Model Configuration (defaults shown) ──────────────────────────────
GEMINI_MODEL=gemini-3.1-pro-preview
CLAUDE_MODEL=claude-sonnet-4-6
EMBEDDING_MODEL=gemini-embedding-001

# ── Claude Proxy (optional) ──────────────────────────────────────────
# ANTHROPIC_BASE_URL=http://localhost:42069

# ── Observability (optional) ──────────────────────────────────────────
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your-langsmith-key-here
LANGSMITH_PROJECT=job-application-agent
```

### User Preferences (`backend/data/user_config.yaml`)

Pydantic-validated preferences controlling job search, matching weights, and scraper config. Editable via `PUT /api/config/preferences` or by editing the YAML file directly.

<details>
<summary>English job search example</summary>

```yaml
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
salary_currency: USD
workplace_types: [remote, hybrid]
experience_level: mid             # entry | mid | senior | lead | executive
employment_types: [FULLTIME]      # FULLTIME | PARTTIME | CONTRACT | INTERNSHIP
date_posted: month                # today | 3days | week | month | all

# Scoring weights (must sum to 1.0)
weights:
  skills: 0.35
  experience: 0.25
  education: 0.15
  location: 0.15
  salary: 0.10

# Scraper sources to use
enabled_sources:
  - arbeitnow
  - greenhouse
  - lever
final_results_count: 10
num_pages_per_source: 5

# Company-specific scraper config (see Scraper Setup Guide below)
greenhouse_board_tokens: [stripe, cloudflare, figma, airbnb]
lever_companies: [netflix, rippling]
workday_urls: []
```
</details>

<details>
<summary>Chinese job search example (中文求职)</summary>

```yaml
job_titles:
  - 软件工程师
  - AI工程师
  - 全栈开发工程师
locations: [北京, 上海, 深圳, 杭州, 远程]
salary_min: 300000
salary_max: 600000
salary_currency: CNY
workplace_types: [remote, hybrid, onsite]
experience_level: mid

# Chinese pipeline settings
ats_mode: auto                    # auto = jieba for Chinese, regex for English
reranker_mode: flashrank-multilingual  # or 'bge' (1GB download) or 'auto'
recruitment_type: social          # social (社招) | campus (校招) | both

# Chinese sources
enabled_sources:
  - tencent
  - netease
  - bytedance
  - jd_campus

# Sources that need manual setup (see Scraper Setup Guide)
# mokahr_org_ids: [org-id-1, org-id-2]
# alibaba_app_key: your-alibaba-key
# boss_zhipin_cookie: your-session-cookie
```
</details>

---

## Scraper Setup Guide

Not all scrapers work out-of-the-box. The table below shows exactly what each source needs.

### Works Immediately (No Setup)

These scrapers use fully public APIs and need zero configuration:

| Source | Market | Config Key | Notes |
|--------|--------|------------|-------|
| `arbeitnow` | Global/EN | — | Public REST API, 5 pages per query |
| `remoteok` | Global/EN | — | Public JSON API, remote jobs only |
| `weworkremotely` | Global/EN | — | RSS feed parsing |
| `tencent` | China | — | Public GET API (腾讯招聘) |
| `netease` | China | — | Public POST API (网易招聘) |
| `jd_campus` | China | — | Public GET API (京东校招), campus/intern only |
| `bytedance` | China | — | Public POST API (字节跳动) |

### Needs API Key (`.env` file)

| Source | Config | Where to Get It | Free Tier? |
|--------|--------|-----------------|------------|
| `jsearch` | `JSEARCH_API_KEY` in `.env` | [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) — sign up, subscribe to free plan, copy API key | Yes (100 req/month) |
| `adzuna` | `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` in `.env` | [Adzuna Developer](https://developer.adzuna.com/) — register for free API access | Yes |

### Needs Company List (`user_config.yaml`)

These scrape from specific company career pages. You must provide the company identifiers.

| Source | Config Key | How to Find Values |
|--------|------------|--------------------|
| `greenhouse` | `greenhouse_board_tokens` | Visit `boards.greenhouse.io/{token}` — the `{token}` is the board slug. Example: `stripe`, `cloudflare`, `figma` |
| `lever` | `lever_companies` | Visit `jobs.lever.co/{company}` — the `{company}` is the slug. Example: `netflix`, `rippling` |
| `workday` | `workday_urls` | Find the company's Workday careers page URL. Example: `https://company.wd5.myworkdayjobs.com/en-US/External` |
| `mokahr` | `mokahr_org_ids` | MokaHR career pages use org IDs in their URL. Inspect the network requests on the company's career page to find the org ID. |

### Needs Manual Credentials (`user_config.yaml`)

These require credentials that must be obtained manually through a browser:

| Source | Config Key | How to Set Up |
|--------|------------|---------------|
| `alibaba` | `alibaba_app_key` | Register on [Alibaba Open Platform](https://open.alibaba.com/), create an app, and copy the app key into `user_config.yaml`. |
| `boss_zhipin` | `boss_zhipin_cookie` | 1. Open [BOSS直聘](https://www.zhipin.com/) in your browser and log in. 2. Open DevTools (F12) → Network tab → copy the `Cookie` header from any request. 3. Paste the full cookie string into `user_config.yaml`. **Expires periodically — must be refreshed.** |

### Fragile / Anti-Scraping (Use With Caution)

These work without auth but may break due to anti-scraping measures:

| Source | Issue | Workaround |
|--------|-------|------------|
| `zhaopin` | Session-based internal API (`fe-api.zhaopin.com`), may require valid cookies | May need browser cookie injection; reliability varies |
| `job51` | Salary text uses font obfuscation (custom TTF fonts) | Built-in `fonttools` decoder handles this, but may break if 51job changes fonts |
| `lagou` | Aggressive anti-scraping (rate limiting, CAPTCHA) | Has built-in session management, but may hit blocks on heavy use |

### Browser-Based Scrapers (Playwright)

These use Playwright to control a real browser. Requires `uv run playwright install chromium` first.

| Source | When It's Used |
|--------|----------------|
| `generic` | Fallback for any career page without a dedicated scraper |
| `workday` | Workday-hosted career pages (requires `workday_urls` config) |

---

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
| `POST` | `/api/config/linkedin-profile` | Upload LinkedIn PDF export for parsing |

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
| Matching (Phase 1) | 73 | Pre-filter, embedder, retriever, scorer, ATS scorer, pipeline, LLM factory |
| Scraping (Phase 2) | 56 | All 18 scrapers, normalizer, dedup, orchestrator |
| DB & API (Phase 3) | 47 | Models, routers (jobs/matches/agent/config), WebSocket, ARQ tasks |
| Agent (Phase 4) | 71 | State, graph routing, field mapper, ATS strategies, interrupt/resume |
| Reports (Phase 6) | 52 | PDF generator, cover letter, templates, evaluation metrics |
| MCP (Phase 7) | 22 | Tools, resources, prompts |
| Docker (Phase 7) | 21 | Compose validation, image builds |
| Config | 16 | Settings, UserConfig, MatchingWeights validation |
| Chinese Pipeline | 256 | Chinese NLP, jieba ATS, BGE/multilingual reranker, 10 Chinese scrapers |
| Integration | 31 | Full user workflow (9-step), E2E scraping/matching |
| Frontend | 36 | Components, stores (Vitest + React Testing Library + MSW) |
| **Total** | **661** | **625 backend + 36 frontend** |

### Running Tests

```bash
# All backend unit tests (no external APIs needed)
cd backend
uv run pytest --ignore=tests/e2e_pipeline_test.py --ignore=tests/test_integration/ -q

# Full backend suite (includes integration tests that need DB/APIs)
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

# Frontend
cd frontend
npx vitest run
```

### E2E Pipeline Test

`e2e_pipeline_test.py` runs the full pipeline against live APIs for both English and Chinese job markets. Requires a running Claude proxy at `localhost:42069` and a valid Google API key.

```bash
cd backend
uv run python tests/e2e_pipeline_test.py
```

**Phase A (English):** Scrapes Arbeitnow, Greenhouse (20 boards), and Lever (4 companies) for 3 titles (Software Engineer, AI Engineer, Full-stack Developer). Scores with Claude, outputs `E2E_Pipeline_Test_Report.md` and `E2E_Pipeline_Test_Data.json`.

**Phase B (Chinese):** Scrapes Tencent and NetEase for 3 titles (软件工程师, AI工程师, 全栈开发工程师). Auto-detects Chinese resume, uses jieba ATS scoring and FlashRank multilingual reranker. Outputs `E2E_Pipeline_Test_Report_ZH.md` and `E2E_Pipeline_Test_Data_ZH.json`.

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
- **ChromaDB** (vector store) + **FlashRank** / **BGE** (cross-encoder reranking)
- **jieba** (Chinese word segmentation for ATS scoring)
- **FlagEmbedding** (BGE-M3 multilingual embeddings + BGE reranker)
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
