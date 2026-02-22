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
    If check=False, caller can inspect stdout/stderr.
    """
    return subprocess.run(cmd, check=check, text=True, capture_output=True, cwd=cwd)


def is_service_running(cfg: DockerComposeConfig, service: str) -> bool:
    """
    True if docker compose reports a container id for the service.
    """
    cmd = _compose_base_cmd(cfg) + ["ps", "-q", service]
    p = _run(cmd, check=False)
    return p.returncode == 0 and p.stdout.strip() != ""


def get_container_id(cfg: DockerComposeConfig, service: str) -> Optional[str]:
    """
    Return the container id for a compose service, or None.
    """
    cmd = _compose_base_cmd(cfg) + ["ps", "-q", service]
    p = _run(cmd, check=False)
    cid = p.stdout.strip()
    return cid or None


def up(cfg: DockerComposeConfig, *, build: bool = True) -> None:
    """
    Start required services in background.
    Fresh-by-default: use --build so db-init image always matches latest schema.sql.
    """
    cmd = _compose_base_cmd(cfg) + ["up", "-d"]
    if build:
        cmd.append("--build")
    cmd += list(cfg.services)
    _run(cmd, check=True)


def down(cfg: DockerComposeConfig, *, remove_volumes: bool = True) -> None:
    """
    Stop and remove containers. Optionally remove volumes for a clean DB.
    """
    cmd = _compose_base_cmd(cfg) + ["down"]
    if remove_volumes:
        cmd.append("-v")

    # down should not hard-fail if nothing is running
    p = _run(cmd, check=False)
    if p.returncode != 0:
        # compose returns non-zero in some "nothing to do" scenarios; ignore.
        pass


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
        p = _run(["docker", "inspect", "-f", "{{.State.Health.Status}}", cid], check=False)
        status = (p.stdout or "").strip()

        if status == "healthy":
            return
        if status == "unhealthy":
            logs = _run(["docker", "logs", "--tail", "80", cid], check=False).stdout
            raise RuntimeError(f"Service '{service}' became unhealthy.\n\nLast logs:\n{logs}")

        time.sleep(1)

    logs = _run(["docker", "logs", "--tail", "120", cid], check=False).stdout
    raise TimeoutError(f"Timed out waiting for '{service}' to become healthy.\n\nLast logs:\n{logs}")


def wait_for_service_exit(cfg: DockerComposeConfig, service: str, timeout_s: int = 60) -> None:
    """
    Wait for a one-shot service (like db-init) to exit successfully.

    This is optional, but it makes schema readiness deterministic:
    - db can be healthy while db-init is still applying schema.
    """
    cid = get_container_id(cfg, service)
    if not cid:
        # If service isn't present, nothing to wait for.
        return

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        p = _run(["docker", "inspect", "-f", "{{.State.Status}} {{.State.ExitCode}}", cid], check=False)
        out = (p.stdout or "").strip()

        # Expected: "exited 0"
        if out.startswith("exited"):
            parts = out.split()
            exit_code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            if exit_code == 0:
                return
            logs = _run(["docker", "logs", "--tail", "200", cid], check=False).stdout
            raise RuntimeError(f"Service '{service}' exited with code {exit_code}.\n\nLast logs:\n{logs}")

        # running / created
        time.sleep(0.5)

    logs = _run(["docker", "logs", "--tail", "200", cid], check=False).stdout
    raise TimeoutError(f"Timed out waiting for '{service}' to exit.\n\nLast logs:\n{logs}")


def ensure_db_for_tests(cfg: DockerComposeConfig, *, timeout_s: int = 60) -> bool:
    """
    Ensure the DB services are up for integration tests.

    Fresh-by-default behavior:
      - Always bring down the stack with volumes (-v)
      - Always bring it up with --build
      - Always wait for db health
      - If db-init is in services, wait for it to exit (schema applied)

    Returns:
        started_by_tests (bool):
            True  -> tests started the DB (always True in fresh-by-default mode)
            False -> tests cannot manage docker in this environment
    """
    if _in_docker() and os.getenv("ALLOW_DOCKER_FROM_TESTS") != "1":
        return False

    if not _docker_available():
        return False

    # ALWAYS start clean
    down(cfg, remove_volumes=True)

    # Start fresh and rebuild db-init so schema.sql is up-to-date
    up(cfg, build=True)

    # Wait for DB to be healthy
    wait_for_healthy(cfg, "db", timeout_s=timeout_s)

    # If db-init is used, wait until it finishes applying schema
    if "db-init" in cfg.services:
        wait_for_service_exit(cfg, "db-init", timeout_s=timeout_s)

    return True