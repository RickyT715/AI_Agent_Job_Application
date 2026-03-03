"""FastAPI application entry point."""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db_session
from app.routers import agent, config, jobs, matches, reports, resumes, skill_analysis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    settings = get_settings()

    # --- ARQ Redis pool ---
    try:
        from arq import create_pool

        from app.worker.settings import get_redis_settings

        app.state.arq_pool = await create_pool(get_redis_settings())
        logger.info("ARQ Redis pool connected")
    except Exception as e:
        logger.warning(f"Could not connect to Redis (ARQ tasks disabled): {e}")
        app.state.arq_pool = None

    # --- LLM cache ---
    try:
        from langchain_community.cache import SQLiteCache
        from langchain_core.globals import set_llm_cache

        cache_path = settings.data_dir / ".langchain_cache.db"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        set_llm_cache(SQLiteCache(database_path=str(cache_path)))
        logger.info(f"LLM cache initialized at {cache_path}")
    except Exception as e:
        logger.warning(f"Could not initialize LLM cache: {e}")

    # --- LangSmith tracing ---
    if settings.langsmith_tracing:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key.get_secret_value()
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        logger.info(f"LangSmith tracing enabled for project: {settings.langsmith_project}")

    yield

    # --- Shutdown ---
    if getattr(app.state, "arq_pool", None) is not None:
        await app.state.arq_pool.aclose()
        logger.info("ARQ Redis pool closed")


app = FastAPI(
    title="AI Job Application Agent",
    description="AI-powered job matching and application automation",
    version="0.1.0",
    lifespan=lifespan,
)

# Attach limiter to app state for SlowAPI
app.state.limiter = limiter


# --- Rate limit error handler ---
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


# --- Global exception handler ---
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# --- Request logging middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.1f}ms)")
    return response


# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(jobs.router)
app.include_router(matches.router)
app.include_router(agent.router)
app.include_router(reports.router)
app.include_router(resumes.router)
app.include_router(config.router)
app.include_router(skill_analysis.router)


@app.get("/health")
async def health_check(request: Request, db: AsyncSession = Depends(get_db_session)):
    """Health check endpoint with database and Redis status."""
    checks: dict[str, str] = {"api": "healthy"}

    # Check database (uses DI, so test overrides apply)
    try:
        from sqlalchemy import text

        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"

    # Check Redis / ARQ pool
    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is None:
        checks["redis"] = "unavailable"
    else:
        checks["redis"] = "healthy"

    # "unhealthy" = configured but broken → 503; "unavailable" = not configured → ok
    has_unhealthy = any(v == "unhealthy" for v in checks.values())
    overall = "degraded" if has_unhealthy else "healthy"
    status_code = 503 if has_unhealthy else 200
    return JSONResponse(
        content={"status": overall, "checks": checks},
        status_code=status_code,
    )
