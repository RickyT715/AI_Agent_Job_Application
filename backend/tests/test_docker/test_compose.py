"""Tests for Docker Compose configuration validation."""

from pathlib import Path

import pytest
import yaml

COMPOSE_FILE = Path(__file__).parent.parent.parent.parent / "docker-compose.yml"


@pytest.fixture
def compose_config():
    """Load and parse docker-compose.yml."""
    assert COMPOSE_FILE.exists(), f"docker-compose.yml not found at {COMPOSE_FILE}"
    with open(COMPOSE_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestComposeStructure:
    """Tests for docker-compose.yml structure."""

    def test_compose_file_exists(self):
        assert COMPOSE_FILE.exists()

    def test_compose_has_services(self, compose_config):
        assert "services" in compose_config

    def test_all_services_defined(self, compose_config):
        services = compose_config["services"]
        assert "backend" in services
        assert "worker" in services
        assert "frontend" in services
        assert "db" in services
        assert "redis" in services

    def test_exactly_five_services(self, compose_config):
        assert len(compose_config["services"]) == 5

    def test_volumes_defined(self, compose_config):
        assert "volumes" in compose_config
        volumes = compose_config["volumes"]
        assert "postgres_data" in volumes
        assert "redis_data" in volumes
        assert "chroma_data" in volumes


class TestDatabaseService:
    """Tests for db service configuration."""

    def test_db_uses_postgres_16(self, compose_config):
        db = compose_config["services"]["db"]
        assert "postgres:16" in db["image"]

    def test_db_has_healthcheck(self, compose_config):
        db = compose_config["services"]["db"]
        assert "healthcheck" in db

    def test_db_exposes_port(self, compose_config):
        db = compose_config["services"]["db"]
        ports = db.get("ports", [])
        assert any("5432" in str(p) for p in ports)

    def test_db_has_persistent_volume(self, compose_config):
        db = compose_config["services"]["db"]
        volumes = db.get("volumes", [])
        assert any("postgres_data" in str(v) for v in volumes)


class TestRedisService:
    """Tests for redis service configuration."""

    def test_redis_uses_version_7(self, compose_config):
        redis = compose_config["services"]["redis"]
        assert "redis:7" in redis["image"]

    def test_redis_has_healthcheck(self, compose_config):
        redis = compose_config["services"]["redis"]
        assert "healthcheck" in redis


class TestBackendService:
    """Tests for backend service configuration."""

    def test_backend_depends_on_db(self, compose_config):
        backend = compose_config["services"]["backend"]
        depends = backend.get("depends_on", {})
        assert "db" in depends

    def test_backend_depends_on_redis(self, compose_config):
        backend = compose_config["services"]["backend"]
        depends = backend.get("depends_on", {})
        assert "redis" in depends

    def test_backend_db_health_condition(self, compose_config):
        backend = compose_config["services"]["backend"]
        db_dep = backend["depends_on"]["db"]
        assert db_dep.get("condition") == "service_healthy"

    def test_backend_exposes_port_8000(self, compose_config):
        backend = compose_config["services"]["backend"]
        ports = backend.get("ports", [])
        assert any("8000" in str(p) for p in ports)

    def test_backend_has_env_file(self, compose_config):
        backend = compose_config["services"]["backend"]
        assert "env_file" in backend


class TestWorkerService:
    """Tests for worker service configuration."""

    def test_worker_depends_on_db(self, compose_config):
        worker = compose_config["services"]["worker"]
        depends = worker.get("depends_on", {})
        assert "db" in depends

    def test_worker_depends_on_redis(self, compose_config):
        worker = compose_config["services"]["worker"]
        depends = worker.get("depends_on", {})
        assert "redis" in depends

    def test_worker_shares_chroma_volume(self, compose_config):
        worker = compose_config["services"]["worker"]
        volumes = worker.get("volumes", [])
        assert any("chroma_data" in str(v) for v in volumes)


class TestFrontendService:
    """Tests for frontend service configuration."""

    def test_frontend_depends_on_backend(self, compose_config):
        frontend = compose_config["services"]["frontend"]
        depends = frontend.get("depends_on", [])
        assert "backend" in depends

    def test_frontend_exposes_port_3000(self, compose_config):
        frontend = compose_config["services"]["frontend"]
        ports = frontend.get("ports", [])
        assert any("3000" in str(p) for p in ports)
