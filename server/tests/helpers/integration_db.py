
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from src.db.db_utils import DBUtility
from tests.helpers.docker_db import DockerComposeConfig, ensure_db_for_tests, down
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import time





def ensure_tables_exist(db: DBUtility, tables: tuple[str, ...], timeout_s: float = 30.0) -> None:
    schema = db.database
    import time
    deadline = time.time() + timeout_s
    table_sql = text("""
        SELECT COUNT(*) AS c
        FROM information_schema.tables
        WHERE table_schema = :schema
          AND table_name IN :tables
    """)

    last = None
    while time.time() < deadline:
        try:
            with db.connect() as conn:
                c = conn.execute(table_sql, {"schema": schema, "tables": tuple(tables)}).scalar_one()
                if int(c) == len(tables):
                    return
                last = f"have {c}/{len(tables)}"
        except Exception as e:
            last = e
        time.sleep(0.4)

    raise RuntimeError(f"Schema not ready for {tables} in schema '{schema}'. Last: {last}")

@dataclass
class IntegrationDBContext:
    """
    Shared integration DB context for tests.

    Responsibilities:
      - Start docker compose services for tests (db + db-init) if needed
      - Initialize DBUtility singleton once
      - Provide DBUtility instance for test classes
      - Tear down containers if this context started them
    """
    compose_cfg: DockerComposeConfig
    started_by_tests: bool
    db: DBUtility

    @staticmethod
    def up(
        *,
        compose_file: Optional[str] = None,
        project_name: Optional[str] = None,
        timeout_s: int = 60,
    ) -> "IntegrationDBContext":
        # Use test compose by default
        compose_file = compose_file or os.getenv("COMPOSE_FILE", "docker-compose.test.yml")
        project_name = project_name or os.getenv("COMPOSE_PROJECT_NAME", "marketsafe_test")

        compose_cfg = DockerComposeConfig(
            compose_file=compose_file,
            project_name=project_name,
        )

        started = ensure_db_for_tests(compose_cfg, timeout_s=timeout_s)

        # Resolve DB connection settings (defaults match your compose)
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = int(os.getenv("DB_PORT", "3307"))
        dbname = os.getenv("DB_NAME", "marketsafe")
        user = os.getenv("DB_USER", "marketsafe")
        pwd = os.getenv("DB_PASSWORD", "marketsafe")
        driver = os.getenv("DB_DRIVER", "mysql+pymysql")

        DBUtility.reset()

        # DBUtility is a singleton. Initialize only if not already initialized.
        if DBUtility._instance is None:
            DBUtility.initialize(
                host=host,
                port=port,
                database=dbname,
                username=user,
                password=pwd,
                driver=driver,
            )

        db = DBUtility.instance()

        assert db is not None

        return IntegrationDBContext(
            compose_cfg=compose_cfg,
            started_by_tests=started,
            db=db,
        )

    def down(self, *, remove_volumes: bool = True) -> None:
        # Dispose pooled connections
        self.db.dispose()

        DBUtility.reset()

        # Only shut down docker if we started it
        if self.started_by_tests:
            down(self.compose_cfg, remove_volumes=remove_volumes)
