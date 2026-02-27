"""ARQ worker settings.

Run worker: uv run arq app.worker.settings.WorkerSettings
"""

from arq.connections import RedisSettings

from app.config import get_settings
from app.worker.tasks import (
    run_agent,
    run_matching,
    run_scraping,
    shutdown,
    startup,
)


def get_redis_settings() -> RedisSettings:
    """Parse Redis URL into ARQ RedisSettings."""
    settings = get_settings()
    url = settings.redis_url
    # Parse redis://host:port/db
    parts = url.replace("redis://", "").split("/")
    host_port = parts[0]
    database = int(parts[1]) if len(parts) > 1 else 0

    if ":" in host_port:
        host, port_str = host_port.split(":")
        port = int(port_str)
    else:
        host = host_port
        port = 6379

    return RedisSettings(host=host, port=port, database=database)


class WorkerSettings:
    """ARQ worker configuration."""

    functions = [run_scraping, run_matching, run_agent]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = get_redis_settings()
    max_jobs = 5
    job_timeout = 600  # 10 minutes
