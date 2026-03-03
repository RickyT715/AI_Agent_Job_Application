# AI Job Application Agent — Improvement Plan

> **Date**: 2026-03-02
> **Status**: Ready for Implementation
> **Scope**: 43 improvements across 6 sprints, derived from 4-agent deep review of 100+ files

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Sprint 1 — Critical Backend Fixes](#2-sprint-1--critical-backend-fixes)
3. [Sprint 2 — Frontend Functional Bugs](#3-sprint-2--frontend-functional-bugs)
4. [Sprint 3 — Security Hardening](#4-sprint-3--security-hardening)
5. [Sprint 4 — Reliability & Resilience](#5-sprint-4--reliability--resilience)
6. [Sprint 5 — Test Hardening](#6-sprint-5--test-hardening)
7. [Sprint 6 — Cleanup & Polish](#7-sprint-6--cleanup--polish)
8. [File Index](#8-file-index)

---

## 1. Executive Summary

A 4-agent team reviewed the entire codebase and identified 43 concrete improvements. The project has a **strong architectural foundation** — clean layered backend, sophisticated matching pipeline, modern React frontend. The critical gaps are:

- **DB engine leak**: A new connection pool is created on every request
- **Frontend wiring gaps**: Settings, resume upload, and filters are scaffolded but not connected to the backend
- **Zero authentication**: Every endpoint is open, including the browser agent that submits real applications
- **Worker inefficiency**: Skill extraction re-processes the entire jobs table after every scrape

This plan addresses all issues in priority order across 6 sprints.

---

## 2. Sprint 1 — Critical Backend Fixes

### 2.1 Cache the Database Engine (Singleton Pattern)

**File**: `backend/app/db/session.py`
**Problem**: `get_engine()` calls `create_async_engine()` on every invocation. Since `get_db_session()` calls `get_session_factory()` which calls `get_engine()`, a **new connection pool is created per request**. This will exhaust database connections under any real load.

**Fix**:
```python
# backend/app/db/session.py

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(database_url: str | None = None) -> AsyncEngine:
    """Get or create the singleton async database engine."""
    global _engine
    if _engine is None or database_url is not None:
        url = database_url or get_settings().database_url
        _engine = create_async_engine(
            url,
            echo=False,
            future=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=300,
        )
    return _engine


def get_session_factory(database_url: str | None = None) -> async_sessionmaker[AsyncSession]:
    """Get or create the singleton session factory."""
    global _session_factory
    if _session_factory is None or database_url is not None:
        engine = get_engine(database_url)
        _session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Dependency that yields a database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_session_ctx() -> AsyncGenerator[AsyncSession]:
    """Context manager for DB sessions outside of FastAPI DI."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def reset_db() -> None:
    """Reset cached engine/factory (for testing)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
```

**Tests to update**: Any test that patches `get_engine` or `get_session_factory` must call `reset_db()` in teardown.

---

### 2.2 Fix Worker Skill Extraction — Only Process New Jobs

**File**: `backend/app/worker/tasks.py:178-214`
**Problem**: After scraping, lines 211-214 load ALL jobs from the database and re-extract skills for every single one, including jobs that were already processed. This is O(n) on the total database size and will get worse over time.

**Fix**: Track which job IDs were newly inserted during the scraping loop, then only extract skills for those.

```python
# In run_scraping(), replace lines 178-214 with:

    # Persist scraped jobs to database, track new IDs
    new_job_ids: list[int] = []
    async with get_db_session_ctx() as db:
        for posting in all_jobs:
            existing = await db.execute(
                select(Job).where(
                    Job.external_id == posting.external_id,
                    Job.source == posting.source,
                )
            )
            if existing.scalar_one_or_none():
                continue

            job = Job(
                external_id=posting.external_id,
                source=posting.source,
                title=posting.title,
                company=posting.company,
                location=posting.location,
                workplace_type=posting.workplace_type,
                description=posting.description,
                requirements=posting.requirements,
                salary_min=posting.salary_min,
                salary_max=posting.salary_max,
                salary_currency=posting.salary_currency,
                employment_type=posting.employment_type,
                experience_level=posting.experience_level,
                apply_url=posting.apply_url,
                raw_data=posting.raw_data,
            )
            db.add(job)
            await db.flush()
            new_job_ids.append(job.id)

    # Extract skills for newly added jobs ONLY
    if new_job_ids:
        async with get_db_session_ctx() as db:
            for job_id in new_job_ids:
                job = await db.get(Job, job_id)
                if job:
                    await extract_and_persist_skills(db, job)
        logger.info(f"Extracted skills for {len(new_job_ids)} new jobs")
```

---

### 2.3 Fix Path Traversal in Report Download

**File**: `backend/app/routers/reports.py:97-119`
**Problem**: `report_id` is user-supplied and used directly in file path construction. An attacker could use `../../etc/passwd` as `report_id`.

**Fix**:
```python
import re

@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """Download a generated PDF/HTML report."""
    # Sanitize report_id — allow only alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', report_id):
        raise HTTPException(status_code=400, detail="Invalid report ID format")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # ... rest unchanged
```

Apply the same pattern to `backend/app/routers/resumes.py` download endpoints.

---

### 2.4 Hide Sensitive Fields from Preferences API

**File**: `backend/app/routers/config.py:27-57`
**Problem**: `_config_to_response()` returns `boss_zhipin_cookie` and `alibaba_app_key` to any caller.

**Fix**: Mask sensitive fields in the response:
```python
def _config_to_response(config: UserConfig) -> PreferencesResponse:
    """Convert UserConfig to PreferencesResponse."""
    settings = get_settings()
    return PreferencesResponse(
        # ... other fields unchanged ...
        alibaba_app_key="***" if config.alibaba_app_key else "",
        boss_zhipin_cookie="***" if config.boss_zhipin_cookie else "",
    )
```

---

### 2.5 Use `settings.data_dir` for File Paths

**Files**:
- `backend/app/routers/reports.py:30` — `REPORTS_DIR = Path("data/reports")`
- `backend/app/services/resume_generator/client.py:12` — `RESUMES_DIR = Path("data/resumes")`

**Fix**:
```python
# reports.py
from app.config import get_settings
# Remove module-level REPORTS_DIR, compute in functions:
def _get_reports_dir() -> Path:
    return get_settings().data_dir / "reports"

# client.py
def _get_resumes_dir() -> Path:
    return get_settings().data_dir / "resumes"
```

---

## 3. Sprint 2 — Frontend Functional Bugs

### 3.1 Wire Settings Page to Backend API

**File**: `frontend/src/pages/SettingsPage.tsx`
**Problem**: `handleSave()` only sets local state. Preferences are never loaded from or saved to the backend.

**Fix**:
```tsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

export function SettingsPage() {
  const queryClient = useQueryClient();

  const { data: preferences, isLoading } = useQuery({
    queryKey: ["preferences"],
    queryFn: () => api.get<PreferencesResponse>("/config/preferences"),
  });

  const updateMutation = useMutation({
    mutationFn: (updates: Partial<PreferencesResponse>) =>
      api.put<PreferencesResponse>("/config/preferences", updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
    },
  });

  if (isLoading) return <p>Loading preferences...</p>;

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Configure your job search preferences and matching criteria</p>
      </div>
      <PreferencesForm
        preferences={preferences ?? DEFAULT_PREFERENCES}
        onSave={(updated) => updateMutation.mutate(updated)}
      />
      {updateMutation.isSuccess && (
        <p className="save-confirmation">Preferences saved successfully!</p>
      )}
      {updateMutation.isError && (
        <p className="save-error">Failed to save preferences.</p>
      )}
    </div>
  );
}
```

---

### 3.2 Implement Resume File Upload

**File**: `frontend/src/components/PreferencesForm.tsx`
**Problem**: `handleResumeChange` captures filename only, never uploads the file.

**Fix**: Add actual file upload logic:
```tsx
const handleResumeChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const resp = await fetch("/api/config/resume", {
      method: "POST",
      body: formData,
    });
    if (!resp.ok) throw new Error("Upload failed");
    const data = await resp.json();
    setResumeFileName(file.name);
    // Show success with character count
  } catch (err) {
    // Show error to user
  }
};
```

Note: Cannot use the `api.post()` helper here since it sets `Content-Type: application/json`. Must use raw `fetch` with `FormData`.

---

### 3.3 Pass Full Filters to Matches API

**File**: `frontend/src/hooks/use-matches.ts`
**Problem**: Only `min_score` is passed to the API, ignoring `q`, `location`, and `workplace_type`.

**Fix**:
```tsx
export function useMatches(filters: Filters) {
  const params = new URLSearchParams();
  if (filters.minScore) params.set("min_score", String(filters.minScore));
  if (filters.q) params.set("q", filters.q);
  if (filters.location) params.set("location", filters.location);
  if (filters.workplace_type) params.set("workplace_type", filters.workplace_type);

  return useQuery({
    queryKey: ["matches", filters],
    queryFn: () => api.get<PaginatedResponse<MatchResponse>>(
      `/matches?${params.toString()}`
    ),
  });
}
```

Also update the backend `list_matches` endpoint to accept `q`, `location`, and `workplace_type` query parameters (join with Job table to filter).

---

### 3.4 Fix Co-occurrence Drill-Down Filtering

**File**: `frontend/src/pages/SkillAnalysisPage.tsx:87-111`
**Problem**: Clicking a skill shows ALL co-occurrences from the report, not filtered by the selected skill.

**Fix**: Fetch co-occurrences on demand using the API, or filter client-side:
```tsx
// Option A: Call the co-occurrence API endpoint when a skill is clicked
const coOccurrences = useQuery({
  queryKey: ["co-occurrences", selectedTitle, drillSkill],
  queryFn: () => api.get(`/skill-analysis/co-occurrences?title=${selectedTitle}&skill=${drillSkill}`),
  enabled: !!drillSkill && !!selectedTitle,
});

// Option B: Filter client-side
const filteredCoOccurrences = report.data?.co_occurrences.filter(
  (c) => c.skill_a === drillSkill || c.skill_b === drillSkill
);
```

---

### 3.5 Add 404 Catch-All Route

**File**: `frontend/src/App.tsx:39-43`

**Fix**:
```tsx
<Routes>
  <Route path="/" element={<DashboardPage />} />
  <Route path="/settings" element={<SettingsPage />} />
  <Route path="/skill-analysis" element={<SkillAnalysisPage />} />
  <Route path="*" element={<Navigate to="/" replace />} />
</Routes>
```

---

## 4. Sprint 3 — Security Hardening

### 4.1 Add API Key Authentication

**New file**: `backend/app/core/auth.py`

Implement simple API key authentication as a FastAPI dependency. This is appropriate for a single-user application and can be extended to JWT later.

```python
"""Simple API key authentication."""

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """Validate the API key from the X-API-Key header."""
    settings = get_settings()
    if not settings.api_key:
        # No key configured = auth disabled (development mode)
        return "dev"
    if api_key != settings.api_key.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
```

**Config change** (`backend/app/config.py`):
```python
class Settings(BaseSettings):
    # ... existing fields ...
    api_key: SecretStr = SecretStr("")  # Empty = auth disabled
```

**Router changes**: Add `Depends(require_api_key)` to sensitive endpoints:
- All `/api/agent/*` endpoints
- All `/api/config/*` endpoints
- `POST /api/jobs/scrape`
- `POST /api/matches/run`

Public endpoints (GET `/api/jobs`, GET `/api/matches`, `/health`) remain open.

**Frontend change** (`frontend/src/api/client.ts`):
```typescript
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": import.meta.env.VITE_API_KEY ?? "",
      ...options?.headers,
    },
    ...options,
  });
  // ...
}
```

---

### 4.2 Escape LIKE Wildcards in User Input

**Files**: `backend/app/routers/jobs.py:33-38`, `backend/app/services/analysis/skill_market.py:80,139,205`

**Fix**: Create a utility function and apply it everywhere:

```python
# backend/app/core/utils.py
def escape_like(value: str) -> str:
    """Escape SQL LIKE special characters in user input."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
```

Usage:
```python
from app.core.utils import escape_like

# In jobs.py:
if q:
    safe_q = escape_like(q)
    query = query.where(
        Job.title.ilike(f"%{safe_q}%") | Job.description.ilike(f"%{safe_q}%")
    )

# In skill_market.py:
safe_pattern = escape_like(title_pattern)
job_ids_sq = (
    select(Job.id)
    .where(func.lower(Job.title).like(f"%{safe_pattern.lower()}%"))
    .subquery()
)
```

---

### 4.3 Externalize Docker Credentials

**File**: `docker-compose.yml`

**Fix**: Replace hardcoded credentials with environment variable references:
```yaml
services:
  db:
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-job_agent}
```

Update `.env.example` with the variables.

---

### 4.4 Add File Upload Size Limits

**File**: `backend/app/routers/config.py:100,143`

**Fix**:
```python
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile, db: AsyncSession = Depends(get_db_session)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    # ... rest unchanged
```

---

### 4.5 Restrict Docker Service Ports

**File**: `docker-compose.yml`

**Fix**: Bind internal services to `127.0.0.1` only:
```yaml
  db:
    ports:
      - "127.0.0.1:5432:5432"
  redis:
    ports:
      - "127.0.0.1:6379:6379"
  resume-generator:
    ports:
      - "127.0.0.1:48765:8000"
```

Only `frontend` (3000) and optionally `backend` (8000) should be publicly accessible.

---

### 4.6 Add Redis Authentication

**File**: `docker-compose.yml`

```yaml
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD:-redis_secret}
    ports:
      - "127.0.0.1:6379:6379"
```

Update `backend/app/config.py`:
```python
redis_url: str = "redis://:redis_secret@localhost:6379/0"
```

---

### 4.7 Make CORS Origins Configurable

**Files**: `backend/app/config.py`, `backend/app/main.py:105-111`

**Fix**:
```python
# config.py
class Settings(BaseSettings):
    # ... existing ...
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

# main.py
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 5. Sprint 4 — Reliability & Resilience

### 5.1 Implement Match Trigger & Rescore Endpoints

**File**: `backend/app/routers/matches.py:70-87`
**Problem**: Both endpoints return fake task IDs without doing anything.

**Fix**:
```python
@router.post("/run", response_model=TaskStatusResponse)
async def trigger_matching(request: Request, body: MatchRunRequest | None = None):
    """Trigger the matching pipeline as a background task."""
    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is None:
        raise HTTPException(status_code=503, detail="Task queue unavailable")

    user_id = body.user_id if body else 1
    job = await arq_pool.enqueue_job("run_matching", user_id=user_id)
    return TaskStatusResponse(task_id=job.job_id, status="queued")


@router.post("/{match_id}/rescore", response_model=TaskStatusResponse)
async def rescore_match(request: Request, match_id: int):
    """Re-run scoring for a specific match."""
    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is None:
        raise HTTPException(status_code=503, detail="Task queue unavailable")

    job = await arq_pool.enqueue_job("run_rescore", match_id=match_id)
    return TaskStatusResponse(task_id=job.job_id, status="queued")
```

Also implement `run_rescore` in `backend/app/worker/tasks.py`.

---

### 5.2 Fix ResumeGeneratorClient Connection Pooling

**File**: `backend/app/services/resume_generator/client.py`
**Problem**: Every method creates and destroys an httpx client.

**Fix**: Use an async context manager pattern:
```python
class ResumeGeneratorClient:
    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or get_settings().resume_generator_url).rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.close()

    async def health_check(self) -> dict:
        client = await self._get_client()
        resp = await client.get("/health")
        if resp.status_code != 200:
            raise ResumeGeneratorError(resp.status_code, resp.text)
        return resp.json()

    # ... same pattern for all other methods, removing `async with self._client()` ...
```

---

### 5.3 Add Meaningful Health Check

**File**: `backend/app/main.py:123-126`

**Fix**:
```python
@app.get("/health")
async def health_check():
    """Health check with dependency status."""
    checks = {"api": "healthy"}

    # Check DB
    try:
        async with get_db_session_ctx() as db:
            await db.execute(select(1))
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"

    # Check Redis
    arq_pool = getattr(app.state, "arq_pool", None)
    if arq_pool:
        try:
            await arq_pool.ping()
            checks["redis"] = "healthy"
        except Exception:
            checks["redis"] = "unhealthy"
    else:
        checks["redis"] = "unavailable"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    status_code = 200 if overall == "healthy" else 503
    return JSONResponse({"status": overall, "checks": checks}, status_code=status_code)
```

---

### 5.4 Add Worker Retry Logic

**File**: `backend/app/worker/settings.py`

**Fix**:
```python
class WorkerSettings:
    functions = [run_scraping, run_matching, run_agent]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = get_redis_settings()
    max_jobs = 5
    job_timeout = 600
    max_tries = 3           # Retry failed tasks up to 3 times
    retry_delay = 30        # Wait 30 seconds between retries
    health_check_interval = 30
```

---

### 5.5 Preserve Exception Chains

**File**: `backend/app/routers/config.py:77,90`

**Fix**:
```python
# Line 77
raise HTTPException(status_code=422, detail=str(e)) from e

# Line 90
raise HTTPException(status_code=422, detail=str(e)) from e
```

---

## 6. Sprint 5 — Test Hardening

### 6.1 Consolidate DB Test Fixtures

Move the duplicated `db_engine`/`db_session` fixtures from 5 separate conftest files into the root `backend/tests/conftest.py`:

```python
# backend/tests/conftest.py (add to existing)

@pytest.fixture
async def db_engine():
    """Shared in-memory SQLite engine for all tests."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.models import Base  # import your declarative base

    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Shared DB session for all tests."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
```

Remove duplicate definitions from:
- `backend/tests/test_db/conftest.py`
- `backend/tests/test_api/conftest.py`
- `backend/tests/test_analysis/conftest.py`
- `backend/tests/test_resume_generator/test_router.py`
- `backend/tests/test_matching/test_skill_persistence.py`

---

### 6.2 Add Error Path Tests for Worker Tasks

**New file**: `backend/tests/test_worker/test_error_paths.py`

Test scenarios:
- DB connection failure during scraping job persistence
- Scorer exception mid-pipeline (verify partial results are handled)
- ChromaDB unavailable during embedding
- Task timeout behavior
- ARQ retry on transient failures

---

### 6.3 Expand Frontend Test Coverage

**New/updated test files**:
- `frontend/src/__tests__/components/MatchDetail.test.tsx` — Test rendering, score display, sub-component composition
- `frontend/src/__tests__/App.test.tsx` — Test routing between pages, 404 redirect
- `frontend/src/__tests__/api/client.test.ts` — Test error parsing, request cancellation
- Update `frontend/src/__tests__/mocks/handlers.ts` — Add MSW handlers for `/api/resumes/*`, `/api/skill-analysis/*`, `/api/config/preferences`

---

### 6.4 Add API Input Validation Tests

**New file**: `backend/tests/test_api/test_input_validation.py`

Test scenarios:
- LIKE wildcard characters in search query (`%`, `_`)
- Negative `match_id` and `job_id` values
- Oversized file upload (>10MB after size limit is added)
- Invalid file types for resume upload
- Malformed JSON in request bodies
- Out-of-range pagination parameters

---

## 7. Sprint 6 — Cleanup & Polish

### 7.1 Delete Dead Code

- **Delete** `frontend/src/main.ts` and `frontend/src/counter.ts` (unused Vite scaffolding)
- **Delete or use** `frontend/src/hooks/use-jobs.ts` (defined but never imported)
- **Remove** `sidebarOpen` / `toggleSidebar` from `frontend/src/stores/app-store.ts`
- **Delete or integrate** `backend/app/core/exceptions.py` (never imported)

### 7.2 Standardize Inline Styles

Move inline `style={{}}` from `ResumeGenerator.tsx` and `SkillAnalysisPage.tsx` to CSS classes in `frontend/src/style.css`.

### 7.3 Add React Error Boundary

**New file**: `frontend/src/components/ErrorBoundary.tsx`

Wrap `<Routes>` in `App.tsx` with the error boundary to prevent full-app crashes on rendering errors.

### 7.4 Make WebSocket URL Configurable

**File**: `frontend/src/hooks/use-agent-ws.ts:7`

```tsx
const WS_BASE = import.meta.env.VITE_WS_URL ?? `ws://${window.location.host}`;
```

### 7.5 Add `delete` Method to API Client

**File**: `frontend/src/api/client.ts`

```typescript
export const api = {
  // ... existing ...
  delete: <T>(path: string) =>
    request<T>(path, { method: "DELETE" }),
};
```

### 7.6 Fix QueryClient Retry Policy

**File**: `frontend/src/App.tsx:8-10`

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 2, staleTime: 30_000 },
  },
});
```

---

## 8. File Index

All files that need modification, grouped by sprint:

### Sprint 1 (Critical)
| File | Action | Section |
|------|--------|---------|
| `backend/app/db/session.py` | Rewrite | 2.1 |
| `backend/app/worker/tasks.py` | Edit (lines 178-214) | 2.2 |
| `backend/app/routers/reports.py` | Edit (line 98) | 2.3 |
| `backend/app/routers/resumes.py` | Edit (download endpoints) | 2.3 |
| `backend/app/routers/config.py` | Edit (lines 55-56) | 2.4 |
| `backend/app/services/resume_generator/client.py` | Edit (line 12) | 2.5 |

### Sprint 2 (Frontend)
| File | Action | Section |
|------|--------|---------|
| `frontend/src/pages/SettingsPage.tsx` | Rewrite | 3.1 |
| `frontend/src/components/PreferencesForm.tsx` | Edit (resume handler) | 3.2 |
| `frontend/src/hooks/use-matches.ts` | Edit | 3.3 |
| `backend/app/routers/matches.py` | Edit (add filter params) | 3.3 |
| `frontend/src/pages/SkillAnalysisPage.tsx` | Edit (co-occurrence) | 3.4 |
| `frontend/src/App.tsx` | Edit (add catch-all route) | 3.5 |

### Sprint 3 (Security)
| File | Action | Section |
|------|--------|---------|
| `backend/app/core/auth.py` | New | 4.1 |
| `backend/app/config.py` | Edit (add api_key) | 4.1 |
| `backend/app/routers/*.py` | Edit (add auth dep) | 4.1 |
| `frontend/src/api/client.ts` | Edit (add API key header) | 4.1 |
| `backend/app/core/utils.py` | New | 4.2 |
| `backend/app/routers/jobs.py` | Edit (escape LIKE) | 4.2 |
| `backend/app/services/analysis/skill_market.py` | Edit (escape LIKE) | 4.2 |
| `docker-compose.yml` | Edit | 4.3, 4.5, 4.6 |
| `.env.example` | Edit | 4.3 |
| `backend/app/main.py` | Edit (CORS) | 4.7 |

### Sprint 4 (Reliability)
| File | Action | Section |
|------|--------|---------|
| `backend/app/routers/matches.py` | Edit (lines 70-87) | 5.1 |
| `backend/app/worker/tasks.py` | Edit (add run_rescore) | 5.1 |
| `backend/app/services/resume_generator/client.py` | Rewrite | 5.2 |
| `backend/app/main.py` | Edit (health check) | 5.3 |
| `backend/app/worker/settings.py` | Edit | 5.4 |

### Sprint 5 (Tests)
| File | Action | Section |
|------|--------|---------|
| `backend/tests/conftest.py` | Edit (add DB fixtures) | 6.1 |
| `backend/tests/test_db/conftest.py` | Edit (remove duplication) | 6.1 |
| `backend/tests/test_api/conftest.py` | Edit (remove duplication) | 6.1 |
| `backend/tests/test_worker/test_error_paths.py` | New | 6.2 |
| `frontend/src/__tests__/components/MatchDetail.test.tsx` | New | 6.3 |
| `frontend/src/__tests__/App.test.tsx` | New | 6.3 |
| `backend/tests/test_api/test_input_validation.py` | New | 6.4 |

### Sprint 6 (Cleanup)
| File | Action | Section |
|------|--------|---------|
| `frontend/src/main.ts` | Delete | 7.1 |
| `frontend/src/counter.ts` | Delete | 7.1 |
| `frontend/src/hooks/use-jobs.ts` | Delete or integrate | 7.1 |
| `frontend/src/stores/app-store.ts` | Edit (remove unused) | 7.1 |
| `frontend/src/components/ErrorBoundary.tsx` | New | 7.3 |
| `frontend/src/hooks/use-agent-ws.ts` | Edit | 7.4 |
| `frontend/src/api/client.ts` | Edit (add delete) | 7.5 |
| `frontend/src/App.tsx` | Edit (retry policy) | 7.6 |
