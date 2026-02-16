# server/tests/helpers/docker_db.py
from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class DockerComposeConfig:
    """
    Configuration for managing a test database via docker compose.

    compose_file:
        Path to docker-compose.test.yml (relative to server/ root).
    project_name:
        Separate project name to avoid clashing with your dev stack.
    services:
        Which services to start for tests (db + db-init usually).
    """
    compose_file: str = "docker-compose.test.yml"
    project_name: str = "marketsafe_test"
    services: tuple[str, ...] = ("db", "db-init")


def _in_docker() -> bool:
    """
    Detect if tests are running inside a container.
    If inside docker, we typically should NOT try to run docker compose,
    unless explicitly allowed by env var.
    """
    return os.path.exists("/.dockerenv") or os.getenv("RUNNING_IN_DOCKER") == "1"


def _docker_available() -> bool:
    """Return True if docker CLI is available and usable."""
    try:
        subprocess.run(
            ["docker", "version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False

def _server_root() -> Path:
    """
    server/tests/helpers/docker_db.py -> parents[2] == server/
    """
    return Path(__file__).resolve().parents[2]

def _compose_base_cmd(cfg: DockerComposeConfig) -> list[str]:
    """
    Base docker compose command using the test compose file and isolated project name.
    Resolves compose_file relative to server/ root so it works from any CWD.
    """
    compose_path = Path(cfg.compose_file)

    if not compose_path.is_absolute():
        compose_path = _server_root() / compose_path

    return ["docker", "compose", "-f", str(compose_path), "-p", cfg.project_name]


def _run(cmd: list[str], *, check: bool = True, cwd: str | None = None):
    """
    Run a subprocess command with consistent defaults.
    """
    return subprocess.run(cmd, check=check, text=True, capture_output=not check, cwd=cwd)

def is_service_running(cfg: DockerComposeConfig, service: str) -> bool:
    """
    True if docker compose reports a container id for the service.
    """
    cmd = _compose_base_cmd(cfg) + ["ps", "-q", service]
    p = subprocess.run(cmd, text=True, capture_output=True)
    return p.returncode == 0 and p.stdout.strip() != ""


def up(cfg: DockerComposeConfig) -> None:
    """
    Start required services in background.
    """
    cmd = _compose_base_cmd(cfg) + ["up", "-d", *cfg.services]
    _run(cmd, check=True)


def down(cfg: DockerComposeConfig, *, remove_volumes: bool = True) -> None:
    """
    Stop and remove containers. Optionally remove volumes for a clean DB.
    """
    cmd = _compose_base_cmd(cfg) + ["down"]
    if remove_volumes:
        cmd.append("-v")
    _run(cmd, check=True)


def get_container_id(cfg: DockerComposeConfig, service: str) -> Optional[str]:
    """
    Return the container id for a compose service, or None.
    """
    cmd = _compose_base_cmd(cfg) + ["ps", "-q", service]
    p = subprocess.run(cmd, text=True, capture_output=True)
    cid = p.stdout.strip()
    return cid or None


def wait_for_healthy(cfg: DockerComposeConfig, service: str = "db", timeout_s: int = 60) -> None:
    """
    Wait until the service container reports healthy.

    Requires:
      - db service has a healthcheck in docker-compose.test.yml
    """
    cid = get_container_id(cfg, service)
    if not cid:
        raise RuntimeError(f"Service '{service}' container not found. Is it started?")

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        p = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Health.Status}}", cid],
            text=True,
            capture_output=True,
        )
        status = p.stdout.strip()

        if status == "healthy":
            return
        if status == "unhealthy":
            # show last logs to help debugging
            logs = subprocess.run(["docker", "logs", "--tail", "50", cid], text=True, capture_output=True)
            raise RuntimeError(
                f"Service '{service}' became unhealthy.\n\nLast logs:\n{logs.stdout}"
            )

        time.sleep(1)

    logs = subprocess.run(["docker", "logs", "--tail", "80", cid], text=True, capture_output=True)
    raise TimeoutError(
        f"Timed out waiting for '{service}' to become healthy.\n\nLast logs:\n{logs.stdout}"
    )


def ensure_db_for_tests(cfg: DockerComposeConfig, *, timeout_s: int = 60) -> bool:
    """
    Ensure the DB services are up for integration tests.

    Returns:
        started_by_tests (bool):
            True  -> tests started the DB (so tests should shut it down in tearDownClass)
            False -> DB was already running OR tests cannot manage docker in this environment

    Behavior:
        - If running inside Docker, we do NOT run docker compose by default.
          To allow it, set: ALLOW_DOCKER_FROM_TESTS=1
        - If docker CLI isn't available, do nothing and return False.
        - If db service is already running, do nothing and return False.
        - Otherwise, start services and wait for db healthcheck.
    """
    if _in_docker() and os.getenv("ALLOW_DOCKER_FROM_TESTS") != "1":
        # Inside containers we usually connect to an already-running db service
        return False

    if not _docker_available():
        return False

    if is_service_running(cfg, "db"):
        return False

    up(cfg)
    wait_for_healthy(cfg, "db", timeout_s=timeout_s)

    # If db-init is part of cfg.services, compose will run it.
    # We can optionally verify it's completed by checking it exists/running:
    # - If db-init is "no restart" it might exit quickly; that's fine.

    return True