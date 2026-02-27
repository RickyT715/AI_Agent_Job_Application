# AI-Powered Job Application Agent: Complete Technical Plan

**This document is an implementation-ready blueprint for building an end-to-end AI job application agent** — from scraping job boards to auto-filling applications — using Python, LangChain, FastAPI, React, and modern AI tooling. Every technology choice below reflects current best practices as of early 2026 and is justified against alternatives. The system architecture follows a modular, event-driven design: a FastAPI backend orchestrates LangChain-powered matching and LangGraph-based browser agents, backed by PostgreSQL and ChromaDB, with a React dashboard for human oversight. The entire stack runs in Docker Compose and exposes MCP tools for integration with Claude Desktop, Cursor, and other AI clients.

---

## 1. Job scraping and search module

### Browser automation: Playwright wins decisively

**Playwright** (Python, `pip install playwright`, v1.49+) is the clear choice over Selenium and Puppeteer for this project. Playwright ships its own browser binaries, eliminating WebDriver version mismatch issues that plague Selenium. Its built-in auto-wait mechanism removes the need for explicit sleep/wait calls, and **browser contexts** enable lightweight isolated sessions far cheaper than launching new browser instances. Playwright supports Chromium, Firefox, and WebKit from a single API, and its network interception capabilities are essential for capturing ATS API calls under the hood.

Selenium's extra WebDriver protocol layer makes it slower and more fragile for modern SPAs. Puppeteer only supports Chromium and has no official Python binding (Pyppeteer is unmaintained). Playwright's Microsoft backing and active development seal the decision.

For stealth against bot detection, use **patchright** (`pip install patchright`) which patches Playwright at the source level, fixing the `Runtime.enable` CDP leak. Pair with `channel="chrome"` (real Chrome, not Chromium) and randomized human-like delays. For production scraping at scale, add residential proxy rotation via Bright Data or SmartProxy.

### Job board API strategy: a tiered approach

Not all job boards offer APIs. The implementation uses a **three-tier strategy**:

**Tier 1 — Direct ATS APIs (structured, reliable):**
- **Greenhouse Job Board API**: Public endpoints at `boards-api.greenhouse.io/v1/boards/{token}/jobs`. Supports programmatic application submission via `POST` with multipart resume upload. Authentication via API key in Basic Auth header. Rate limit: 50 requests/10 seconds.
- **Lever Postings API**: Completely public, no auth needed. `GET https://api.lever.co/v0/postings/{company}` returns JSON of all published jobs. Application submission via `POST` requires an API key but is straightforward.
- These APIs return clean, structured JSON — no scraping needed.

**Tier 2 — Aggregator APIs (broad coverage, cost-effective):**
- **JSearch (RapidAPI)**: Real-time job search powered by Google for Jobs. Returns up to 500 results per query including LinkedIn, Indeed, and Glassdoor listings. Free tier available. This is the **primary discovery channel** since it covers multiple boards with a single API.
- **Adzuna API**: Covers 16+ countries with salary data and trend analytics. Free tier with `app_id` + `app_key` authentication.
- **Arbeitnow API**: Free public endpoint aggregating from Greenhouse, Lever, Workable, and others. Includes remote/visa sponsorship filters.

**Tier 3 — Browser automation (last resort):**
- **Workday**: No public API. Intercept internal XHR requests to Workday's search endpoint via Playwright's `route()` method. URL pattern: `https://{company}.wd{N}.myworkdayjobs.com/`.
- **LinkedIn**: Explicitly prohibited by ToS. **Do not scrape LinkedIn directly.** The HiQ v. LinkedIn case (resolved 2022) established that while public scraping doesn't violate the CFAA, it constitutes breach of contract under LinkedIn's User Agreement. Instead, use JSearch which indexes LinkedIn job postings via Google for Jobs.
- **Indeed**: The Publisher API is deprecated. Use JSearch or Adzuna as alternatives.

### Normalized job data schema

All sources are normalized into a single Pydantic model that follows the Schema.org `JobPosting` vocabulary:

```python
class JobPosting(BaseModel):
    id: str                           # Internal UUID
    external_id: str                  # Source platform's ID
    source: str                       # "greenhouse", "lever", "jsearch", etc.
    source_url: str                   # Original posting URL
    apply_url: str                    # Direct application URL
    title: str
    company_name: str
    description: str                  # Full text description
    location: str
    workplace_type: str               # "remote" | "hybrid" | "onsite"
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_currency: Optional[str]
    employment_type: str              # "FULLTIME" | "CONTRACT" | "INTERN"
    required_skills: list[str]        # Extracted via LLM
    preferred_skills: list[str]
    years_experience: Optional[int]
    education_level: Optional[str]
    ats_platform: Optional[str]
    posted_at: datetime
    scraped_at: datetime
```

Deduplication uses a composite key of `(company_name, title, location)` across sources. Many ATS platforms embed `@type: "JobPosting"` structured data in page HTML, which can be extracted directly using `json-ld` parsing before falling back to LLM-based extraction.

---

## 2. AI matching engine with LangChain

### LangChain 2026 architecture fundamentals

The project uses **LangChain v1.2.x** with its current modular package structure: `langchain-core` for base abstractions, `langchain-openai` for OpenAI integration, `langchain-anthropic` for Claude, and `langchain-chroma` for the vector store. **LCEL (LangChain Expression Language)** is the composition paradigm — the pipe operator `|` chains Runnables into declarative pipelines: `prompt | model | parser`. Every component implements `.invoke()`, `.stream()`, `.batch()`, and async variants.

**AgentExecutor is officially deprecated.** All agent workflows use **LangGraph**, which provides graph-based state management, built-in persistence via checkpointers, and first-class human-in-the-loop support. For the matching pipeline specifically (which is a deterministic chain, not a conversational agent), LCEL chains are sufficient and preferred.

### Two-stage retrieval + reranking pipeline

The matching engine operates in two stages to balance **recall** (finding all possible matches) with **precision** (ranking the best ones):

**Stage 1 — Vector similarity retrieval** embeds both the user's resume and all job postings into a shared vector space, then retrieves the top-k (k=30) most similar jobs by cosine similarity. This is fast and catches semantic matches that keyword search would miss.

**Stage 2 — Cross-encoder reranking** takes those 30 candidates and reranks them using a more expensive but accurate model, narrowing to the top 5-10. The implementation uses LangChain's `ContextualCompressionRetriever`:

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import FlashrankRerank
from langchain_chroma import Chroma

# Stage 1: broad retrieval
retriever = vectorstore.as_retriever(search_kwargs={"k": 30})

# Stage 2: precise reranking
compressor = FlashrankRerank(top_n=10)

# Combined pipeline
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, base_retriever=retriever
)
results = compression_retriever.invoke(resume_text)
```

**FlashRank** is chosen over Cohere Rerank because it runs locally, is CPU-only, requires no API key, and costs nothing — ideal for a portfolio project. For higher accuracy in production, swap in `CohereRerank` (which costs $1/1K searches) or `bge-reranker-base` from BAAI (free, but needs GPU for speed).

### Embedding model: OpenAI text-embedding-3-small

For job-resume matching at portfolio scale (~1,000-10,000 job postings):

| Model | MTEB Score | Cost | Verdict |
|-------|-----------|------|---------|
| **OpenAI text-embedding-3-small** | ~62.3 | **$0.02/1M tokens** | ✅ Best balance |
| OpenAI text-embedding-3-large | ~64.6 | $0.13/1M tokens | Marginal gain, 6.5x cost |
| BGE-M3 (BAAI) | ~63.0 | Free (self-hosted) | Great if privacy matters |
| Cohere embed-v4 | ~65.2 | $0.12/1M tokens | Best quality, higher cost |

**text-embedding-3-small** wins for this project: at portfolio scale the total embedding cost is pennies, LangChain integration is one line (`OpenAIEmbeddings(model="text-embedding-3-small")`), and quality is strong. The budget alternative is **BGE-M3** self-hosted via `sentence-transformers`, which is MIT-licensed and free.

### Vector database: ChromaDB for development, Qdrant for production

**ChromaDB** (`pip install chromadb`) is the right choice for local development and portfolio demos. It requires zero configuration — just `Chroma(persist_directory="./chroma_db")` — and handles the scale of this project (under 100K vectors) easily. It persists to a local SQLite file and integrates seamlessly with LangChain via `langchain-chroma`.

For production deployment or if advanced filtering during search is needed, **Qdrant** is the upgrade path. It's 3-4x faster than ChromaDB, supports payload filtering during HNSW traversal (critical for filtering by location, salary range, etc.), and runs as a Docker container. The LangChain abstraction layer makes migration a one-line change.

Pinecone was rejected because it's cloud-only with no local option (minimum $50/month). Weaviate adds unnecessary complexity for this use case.

### LLM-as-Judge scoring with structured output

After retrieval and reranking, the top matches receive detailed scoring via an LLM judge. The implementation uses `with_structured_output()` — LangChain's recommended method for getting reliable structured responses:

```python
from pydantic import BaseModel, Field

class JobMatchScore(BaseModel):
    overall_score: int = Field(ge=1, le=10, description="Overall match 1-10")
    skills_match: int = Field(ge=1, le=10)
    experience_match: int = Field(ge=1, le=10)
    education_match: int = Field(ge=1, le=10)
    missing_skills: list[str] = Field(description="Skills the candidate lacks")
    strengths: list[str] = Field(description="Candidate's strongest points")
    reasoning: str = Field(description="Detailed scoring explanation")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(JobMatchScore)
score = structured_llm.invoke(scoring_prompt)  # Returns validated Pydantic object
```

`with_structured_output()` uses the model's native tool-calling/JSON schema capabilities under the hood. It's preferred over `PydanticOutputParser` (which injects format instructions into the prompt and is less reliable) and `JsonOutputParser` (which lacks Pydantic validation). The scoring rubric uses integer scales (1-10) with chain-of-thought reasoning to improve calibration.

---

## 3. Auto-fill agent using browser-use and LangGraph

### browser-use is the centerpiece library

**browser-use** (`pip install browser-use`, v0.11.2+, 50,000+ GitHub stars, MIT license) is the primary browser automation library for the auto-fill agent. It restructures messy DOM for LLM consumption — stripping irrelevant elements, labeling interactive components, and providing a clean control interface. It scored **89.1% on the WebVoyager benchmark**, outperforming alternatives.

The architecture is an agent loop: the LLM reasons about the current task → generates browser actions → Playwright executes them → screenshots/DOM are fed back to the LLM. browser-use already uses Playwright internally, so it inherits all stealth and performance benefits.

```python
from browser_use import Agent, Browser, Controller
from langchain_openai import ChatOpenAI

controller = Controller()

@controller.action("Upload resume file")
def upload_resume(file_path: str) -> str:
    # Custom action for resume upload
    return f"Uploaded: {file_path}"

agent = Agent(
    task="Fill out the job application at {url} using my resume data",
    llm=ChatOpenAI(model="gpt-4o"),
    browser=Browser(),
    controller=controller,
)
result = await agent.run()
```

**Why browser-use over alternatives:** LangChain's built-in `PlayWrightBrowserToolkit` provides basic tools (navigate, click, extract text) but lacks DOM restructuring for LLMs, screenshot analysis, and intelligent element labeling. Microsoft's Agent-E (AutoGen WebSurfer) is DOM-only with no vision support, and performance drops on dynamic forms. LaVague (Selenium-based) is slower and less actively maintained. browser-use combines the best of all approaches.

### LangGraph for human-in-the-loop orchestration

The auto-fill workflow requires human approval before submission. **LangGraph** provides first-class support for this via `interrupt()` and persistent checkpointers:

```python
from langgraph.types import interrupt, Command

def review_application(state: dict) -> Command:
    """Pause for human review before submitting."""
    decision = interrupt({
        "question": "Ready to submit this application?",
        "preview": {
            "company": state["company_name"],
            "fields_filled": state["form_data"],
            "screenshot": state["screenshot_base64"],
        }
    })
    if decision["approved"]:
        return Command(goto="submit")
    return Command(goto="abort")
```

LangGraph's persistence layer (PostgreSQL checkpointer in production, `MemorySaver` for development) saves agent state across pauses — the user can review on their phone hours later and resume. Thread IDs associate state with specific application sessions, and checkpoints survive server restarts.

### Handling diverse ATS forms

ATS platforms vary dramatically in form structure. **Greenhouse** and **Lever** are clean, single-page forms with standard fields. **Workday** and **Taleo** are multi-page wizards requiring account creation, full work history, and custom screening questions. The agent handles this diversity through browser-use's DOM restructuring (which normalizes different UI frameworks) combined with a **field mapping strategy**:

- Common fields (name, email, phone, LinkedIn URL) are pre-mapped from user profile data
- File uploads use Playwright's `set_input_files()` or `expect_file_chooser()` for hidden inputs
- Custom questions are answered by the LLM using resume context and the matching analysis
- Where direct API submission exists (Greenhouse Job Board API, Lever), bypass browser automation entirely for reliability

---

## 4. Report generation module

### WeasyPrint + Jinja2 for professional PDF reports

**WeasyPrint** (`pip install weasyprint`) converts HTML/CSS to PDF without a browser engine. Combined with **Jinja2** templates, it lets you design reports using familiar web technologies — HTML for structure, CSS Flexbox for layout, and Jinja2 for dynamic data injection. This is dramatically simpler than ReportLab (which requires manual canvas positioning) and more capable than FPDF2 (which lacks HTML/CSS support entirely).

```python
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

def generate_job_report(match_data: dict) -> bytes:
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("job_report.html")
    rendered = template.render(**match_data)
    return HTML(string=rendered).write_pdf(
        stylesheets=[CSS("styles/report.css")]
    )
```

A job match report includes: **cover page** with overall match score visualization, **score breakdown** across skills/experience/education/location dimensions, **skill gap analysis** (matched skills in green, missing in red, with learning recommendations), **salary market analysis**, **company overview**, **AI-generated talking points** for interviews, and a **tailored cover letter draft**.

### LangChain-powered cover letters

Cover letter generation uses an LCEL chain that incorporates resume data, job description, and the matching analysis:

```python
cover_letter_chain = (
    PromptTemplate.from_template(COVER_LETTER_PROMPT)
    | ChatOpenAI(model="gpt-4o", temperature=0.7)
    | StrOutputParser()
)
letter = cover_letter_chain.invoke({
    "resume_text": resume, "job_title": title,
    "company": company, "matched_skills": skills,
    "key_achievements": achievements,
})
```

The prompt instructs the model to reference specific company values from the job description, highlight relevant resume experiences, and constructively address skill gaps. Temperature is set to **0.7** (higher than scoring at 0.0) to encourage varied, natural writing.

---

## 5. React dashboard frontend

### Technology stack: Vite + React 19 + TypeScript + shadcn/ui

**React 19.2** (released October 2025) is the current stable version, featuring the **React Compiler** (automatic memoization that eliminates 30-60% of unnecessary re-renders), stable Server Components, and the new `<Activity />` component for managing visibility states. Create React App is deprecated; **Vite** is the standard build tool for React SPAs in 2026 — lightning-fast HMR, modern ES module support, and minimal configuration.

**shadcn/ui** is the UI component library choice. Unlike traditional libraries installed as dependencies, shadcn/ui copies accessible, Tailwind CSS-based components directly into your project. This gives full ownership and customization control. It's built on Radix UI primitives (WAI-ARIA accessible) and dominates the 2025-2026 React ecosystem. For a portfolio project, it signals understanding of modern React patterns. Ant Design and MUI were rejected — both are heavier and harder to customize.

### State management: Zustand + TanStack Query

This combination is the **consensus recommendation** across all 2025-2026 sources, replacing Redux Toolkit for most applications:

- **TanStack Query v5** handles all **server/remote state**: job listings, match scores, API data. It provides intelligent caching, background refetching, request deduplication, and optimistic updates — reducing network requests by 40-60% compared to naive approaches.
- **Zustand v5** handles all **client/UI state**: filters, selected job, sidebar state, theme. At **~1KB gzipped** (44x smaller than React itself), it requires zero boilerplate and no context providers.

```typescript
// Zustand for UI state
const useAppStore = create((set) => ({
  filters: { location: '', remote: false, minScore: 0 },
  selectedJobId: null,
  setFilters: (filters) => set({ filters }),
  setSelectedJob: (id) => set({ selectedJobId: id }),
}))

// TanStack Query for server state
const useJobs = (filters) => useQuery({
  queryKey: ['jobs', filters],
  queryFn: () => api.getJobs(filters),
  staleTime: 5 * 60 * 1000,  // 5min cache
})
```

### Type-safe API integration via Orval

**Orval** generates TypeScript API clients with native TanStack Query hooks directly from FastAPI's auto-generated OpenAPI spec. This creates a fully type-safe pipeline: Python Pydantic models → OpenAPI 3.1 → TypeScript types + React Query hooks. Run `npx orval --input http://localhost:8000/openapi.json --output src/api` and get ready-to-use `useJobs()`, `useMatchScore()`, `useApplyJob()` hooks automatically.

### Visualization with Recharts

**Recharts** (24.8K+ GitHub stars) provides the radar chart for multi-dimensional skill matching and bar/line charts for score breakdowns. Its component-based JSX API (`<RadarChart>`, `<BarChart>`) fits React's paradigm naturally. Match scores use color coding: **green** (80-100%), **yellow** (60-79%), **red** (<60%).

WebSocket integration for real-time agent status uses `react-use-websocket`, connecting to FastAPI's native WebSocket endpoint to stream agent actions, form-filling progress, and screenshots to the dashboard in real-time.

---

## 6. Observability and evaluation

### LangSmith for tracing and debugging

**LangSmith** is the primary observability platform, chosen for its seamless LangChain integration — setup requires only three environment variables:

```bash
export LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="lsv2_..."
export LANGSMITH_PROJECT="job-agent"
```

The free Developer tier provides **5,000 traces/month** with 14-day retention, which is sufficient for development and portfolio demos. LangSmith captures full execution trees with nested spans, showing every prompt, completion, tool call, token count, and latency measurement. This is critical for debugging when the auto-fill agent maps wrong resume fields to wrong form fields.

For open-source/self-hosted needs, **Langfuse** (MIT license, 19K+ GitHub stars) is the strongest alternative, offering Docker/Kubernetes deployment, 50K observations/month on cloud, and framework-agnostic integration.

### Evaluation pipeline for matching quality

The evaluation system combines three approaches:

**LangSmith experiments** with custom evaluators measure matching precision and recall against a hand-labeled dataset of 50-100 resume-job pairs:

```python
from langsmith import evaluate

def skill_match_f1(run, example):
    predicted = set(run.outputs.get("matched_skills", []))
    expected = set(example.outputs.get("expected_skills", []))
    tp = len(predicted & expected)
    precision = tp / max(len(predicted), 1)
    recall = tp / max(len(expected), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-6)
    return {"key": "skill_match_f1", "score": f1}

results = evaluate(
    job_matcher_pipeline, data="job-matching-eval",
    evaluators=[skill_match_f1], experiment_prefix="v1",
)
```

**RAGAS** (`pip install ragas`) evaluates the RAG retrieval component specifically — measuring whether the right job postings are retrieved (context precision/recall) and whether match assessments are grounded in actual resume/job data (faithfulness). **Custom NDCG metrics** measure ranking quality: are the best matches ranked highest?

---

## 7. MCP integration for universal AI client access

### What MCP enables

The **Model Context Protocol** (spec version 2025-11-25), originally created by Anthropic and now governed by the Linux Foundation's Agentic AI Foundation, is an open standard that lets any AI application connect to any tool or data source through a single protocol. By wrapping the job agent's functionality as an MCP server, it becomes accessible from **Claude Desktop, ChatGPT, VS Code Copilot, Cursor, Gemini CLI**, and any other MCP-compatible client — without building separate integrations for each.

### Building the MCP server with FastMCP

Use the standalone **FastMCP v3** (`pip install fastmcp`, by PrefectHQ, ~1M downloads/day). It's more feature-rich than the official SDK's built-in FastMCP, supporting server composition, OpenAPI auto-generation, and interactive UIs:

```python
from fastmcp import FastMCP

mcp = FastMCP("JobApplicationAgent")

@mcp.tool
def search_jobs(query: str, location: str = "",
                remote: bool = False, limit: int = 20) -> list[dict]:
    """Search for job listings matching criteria."""
    # Calls the job scraping module internally
    ...

@mcp.tool
def match_resume_to_job(job_id: str) -> dict:
    """Score how well user's resume matches a specific job.
    Returns overall_score, skill_matches, skill_gaps, reasoning."""
    ...

@mcp.tool
def fill_application(job_id: str, dry_run: bool = True) -> dict:
    """Auto-fill a job application. Use dry_run=True to preview."""
    ...

@mcp.resource("resume://current")
def get_resume() -> str:
    """Load the user's current resume for context."""
    ...

@mcp.resource("preferences://job-search")
def get_preferences() -> str:
    """User's job search preferences."""
    ...

@mcp.prompt
def cover_letter_prompt(job_title: str, company: str) -> str:
    """Generate a tailored cover letter."""
    return f"Write a cover letter for {job_title} at {company}..."
```

**Transport**: Use `stdio` for local development (Claude Desktop config points to the server script) and **Streamable HTTP** for remote deployment (a single endpoint at `/mcp` supporting both POST and GET with SSE streams). The older SSE transport is deprecated as of the March 2025 spec.

**Design principle**: Tools for actions (search, score, fill), Resources for context (resume, preferences, application history), Prompts for guided workflows (cover letters, interview prep). Destructive actions like `submit_application` use a `dry_run` parameter defaulting to `True`.

---

## 8. Multi-LLM support and cost optimization

### LangChain's ChatModel abstraction

LangChain provides a uniform `BaseChatModel` interface across all providers. Swapping models is a single-line change:

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

# Same interface: .invoke(), .stream(), .with_structured_output(), .bind_tools()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# llm = ChatAnthropic(model="claude-sonnet-4-20250514")
# llm = ChatOllama(model="llama3.2")

chain = prompt | llm | parser  # Works identically with any model
```

For local/offline use, **Ollama** + `langchain-ollama` supports `with_structured_output()` via native JSON schema mode. Best local models for structured output are **Qwen 2.5** (7B/14B, excellent at structured tasks), **Llama 3.2** (3B, fast), and **Mistral Small** (7B, good JSON compliance).

**LiteLLM** was evaluated as an alternative proxy layer (33K+ GitHub stars, Y Combinator backed) but is overkill for a single-developer project. It becomes valuable at team/enterprise scale for centralized cost tracking and load balancing. For this project, LangChain's native abstractions are simpler and sufficient.

### Task-based model routing saves 40-70% on API costs

Not every task needs GPT-4o. The routing strategy assigns models by task complexity:

| Task | Model | Cost (per 1M input tokens) |
|------|-------|---------------------------|
| Resume/job description parsing | gpt-4o-mini | $0.15 |
| Keyword extraction, classification | gpt-4o-mini or Ollama/Llama 3.2 | $0.15 or free |
| Embedding generation | text-embedding-3-small | $0.02 |
| Detailed match scoring (LLM-as-Judge) | gpt-4o | $2.50 |
| Cover letter generation | gpt-4o or Claude Sonnet | $2.50-$3.00 |
| Browser agent reasoning | gpt-4o | $2.50 |

Additionally, LangChain's `InMemoryCache` or `SQLiteCache` prevents re-processing identical queries, and `.batch()` methods enable bulk operations for efficiency.

---

## 9. Configuration layer

### Two-tier configuration architecture

**Infrastructure config** (database URLs, API keys, feature flags) uses **pydantic-settings v2.13.x** with environment variables and `.env` files, following 12-factor app principles:

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", case_sensitive=False
    )
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobagent"
    REDIS_URL: str = "redis://localhost:6379"
    OPENAI_API_KEY: SecretStr = SecretStr("")
    ANTHROPIC_API_KEY: SecretStr = SecretStr("")
```

**User preferences** (job search criteria, matching weights, autofill behavior) use a **YAML config file** — chosen over TOML because job preferences involve moderate nesting with lists of objects (locations, skills), and YAML handles this more readably. Comments allow inline documentation for users. The YAML file is loaded and validated against Pydantic models:

```yaml
# config.yaml
job_search:
  titles: ["Software Engineer", "AI/ML Engineer", "Full Stack Developer"]
  locations:
    - city: "Toronto"
      remote_ok: true
    - city: "San Francisco"
      remote_ok: true
  work_mode: "remote"
  salary: { min: 100000, max: 180000, currency: "CAD" }

matching:
  skills_weight: 0.35
  experience_weight: 0.25
  location_weight: 0.15
  salary_weight: 0.15
  company_culture_weight: 0.10

autofill:
  mode: "review_first"    # review_first | auto_submit | manual
  cover_letter_generation: true
  max_daily_applications: 10
```

API keys are **never** stored in YAML — only in `.env` files excluded from version control. Pydantic's `SecretStr` type automatically masks values in logs and repr output.

---

## 10. Docker and deployment

### Multi-stage Docker builds with uv

**uv** (by Astral, Rust-based) replaces pip/Poetry as the package manager — it's **10-100x faster** for dependency resolution and is now the standard for Python projects. The backend Dockerfile uses multi-stage builds to produce a minimal production image:

```dockerfile
# Stage 1: Build
FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install deps first (cached layer)
COPY uv.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.13-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH"
RUN useradd -m -s /bin/false appuser
WORKDIR /app
COPY --from=build --chown=appuser:appgroup /app .
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The frontend builds with Node.js and serves via Nginx:

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### Docker Compose orchestrates five services

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/jobagent
      REDIS_URL: redis://redis:6379

  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]

  db:
    image: postgres:16-alpine
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: [qdrant_data:/qdrant/storage]

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
```

### Deployment: Railway or Hetzner VPS

For a portfolio project demo, **Railway** ($5/month, auto-deploy from GitHub, built-in Postgres/Redis) offers the fastest path to deployment. For maximum control and value, a **Hetzner VPS** (~€5-9/month for 2vCPU/4GB) running Docker Compose gives unlimited containers. A GitHub Actions CI/CD pipeline using `astral-sh/setup-uv@v5`, `docker/build-push-action@v6`, and GHA cache handles testing, building, and deployment automatically on push to main.

---

## 11. PostgreSQL database design

### Why PostgreSQL over SQLite

PostgreSQL is chosen over SQLite for three decisive reasons: **JSONB columns** with GIN indexing (essential for storing structured resume data, scoring breakdowns, and agent logs), **concurrent read/write access** (the agent and web UI access the database simultaneously), and **full-text search** via `tsvector/tsquery` (for searching job descriptions). Docker makes PostgreSQL setup trivial. SQLite is retained only for unit tests via SQLAlchemy's database URL abstraction.

### Schema with six core tables

The schema centers on six tables: `users` (profile, structured resume as JSONB, preferences), `jobs` (scraped postings with full-text search index), `match_results` (scores with JSONB breakdown, unique per user-job pair), `applications` (status tracking with timestamps), `cover_letters` (generated letters with model/prompt metadata), and `agent_logs` (every browser action grouped by session UUID). Key indexes include a composite unique index on `(external_id, source)` for job deduplication, a GIN index on `to_tsvector('english', description)` for full-text search, and a covering index on `(user_id, overall_score DESC)` for fast match retrieval.

### SQLAlchemy 2.0 with async PostgreSQL

**SQLAlchemy 2.0.46** uses modern declarative mapping with `Mapped` type annotations and `mapped_column()`. Combined with **asyncpg** as the async PostgreSQL driver:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)  # JSONB on PG
    match_results: Mapped[list["MatchResult"]] = relationship(back_populates="job")
```

**Alembic** manages migrations with auto-generation from model changes: `alembic revision --autogenerate -m "add_cover_letters_table"`. The async template (`alembic init -t async`) integrates with asyncpg. All models must be imported in `env.py` for auto-detection to work — the most common setup pitfall.

---

## 12. FastAPI backend architecture

### Project structure and routing

**FastAPI ~0.128.x** uses a file-type structure with clear separation of concerns:

```
app/
├── main.py              # App init, middleware, router mounting
├── config.py            # Pydantic Settings
├── dependencies.py      # get_db, get_llm, get_settings
├── routers/             # API endpoint definitions
│   ├── jobs.py          # /api/jobs/*
│   ├── matches.py       # /api/matches/*
│   ├── agent.py         # /api/agent/* + WebSocket
│   ├── reports.py       # /api/reports/*
│   └── config.py        # /api/config/*
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response models
├── services/            # Business logic
└── db/                  # Database engine, session factory
```

FastAPI's `Depends()` system injects database sessions, configuration, and LangChain components into endpoints. Sessions are scoped per-request and auto-commit/rollback. Settings are cached with `@lru_cache`.

### Background task processing with ARQ

Long-running tasks (job scraping, batch matching, agent runs) use **ARQ** (`pip install arq`, v0.26.x) — an async Redis queue built for asyncio. It integrates naturally with FastAPI (both use `async def`) and supports retries, deferred execution, and job status tracking. ARQ is preferred over Celery (which is synchronous and requires eventlet/gevent for async) and over FastAPI's built-in `BackgroundTasks` (which runs in the same process with no retry/status support).

```python
from arq import create_pool
from arq.connections import RedisSettings

@router.post("/agent/start")
async def start_agent(job_id: int):
    redis = await create_pool(RedisSettings())
    job = await redis.enqueue_job("run_agent_task", job_id=job_id)
    return {"task_id": job.job_id}
```

### WebSocket for real-time agent status

A `ConnectionManager` pattern broadcasts agent actions to connected dashboard clients:

```python
@router.websocket("/ws/agent-status")
async def agent_status_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

The agent service calls `await manager.broadcast({"action": "filling_form", "field": "email", "progress": 45})` at each step, and the React dashboard renders progress in real-time via `react-use-websocket`.

Middleware includes CORS (configured for Vite dev server at `:5173`), request logging with duration timing, global exception handling returning structured JSON errors, and optional rate limiting via SlowAPI for production.

---

## Conclusion: how the pieces connect

This system's architecture flows in a clear pipeline. The **scraping module** feeds normalized job data into PostgreSQL and ChromaDB. The **matching engine** uses a two-stage retrieval + LLM-as-Judge pipeline to score matches. The **React dashboard** displays results with real-time WebSocket updates. When the user approves a match, the **auto-fill agent** (browser-use + LangGraph) navigates to the ATS, fills the application, and pauses for human review before submission. The **MCP server** wraps everything for universal AI client access. **LangSmith** traces every decision for debugging and evaluation.

Three architectural decisions deserve emphasis. First, **browser-use over raw Playwright tools** for the auto-fill agent — the DOM restructuring and element labeling it provides are essential for LLM-driven form interaction, and building this from scratch would consume weeks of development time. Second, **LCEL chains for matching, LangGraph for agents** — using the right LangChain primitive for each task type keeps the codebase clean and leverages each tool's strengths. Third, **MCP as the integration layer** — a single MCP server instantly makes the entire system accessible from Claude Desktop, Cursor, VS Code Copilot, and ChatGPT, multiplying the project's portfolio impact far beyond a standalone web app.

For a new grad portfolio project, this stack demonstrates mastery of modern AI infrastructure (LangChain, LangGraph, vector databases, embeddings), full-stack development (FastAPI, React 19, PostgreSQL, Docker), and emerging standards (MCP) — precisely the combination that AI/full-stack roles are hiring for in 2026.