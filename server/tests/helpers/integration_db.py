from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from src.db.db_utils import DBUtility
from tests.helpers.docker_db import DockerComposeConfig, ensure_db_for_tests, down


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

        # Only shut down docker if we started it
        if self.started_by_tests:
            down(self.compose_cfg, remove_volumes=remove_volumes)


# =========================================================
# Email Verification Token Helpers
# =========================================================

def setup_tokens_table(db: DBUtility) -> None:
    """Ensure the email_verification_tokens table exists."""
    from sqlalchemy import text
    
    sql = text("""
        CREATE TABLE IF NOT EXISTS email_verification_tokens (
            id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            account_id     BIGINT UNSIGNED NOT NULL,
            token_hash     VARCHAR(255)    NOT NULL,
            created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at     DATETIME        NOT NULL,
            used           BOOLEAN         NOT NULL DEFAULT FALSE,
            used_at        DATETIME        NULL,
            
            PRIMARY KEY (id),
            KEY idx_email_token_hash (token_hash),
            KEY idx_email_token_account (account_id, used)
        ) ENGINE=InnoDB;
    """)
    
    try:
        with db.transaction() as conn:
            conn.execute(sql)
    except Exception:
        pass  # Table likely already exists


def clear_tokens_table(db: DBUtility) -> None:
    """Clear all tokens from the table for clean test state."""
    from sqlalchemy import text
    
    sql = text("DELETE FROM email_verification_tokens")
    
    try:
        with db.transaction() as conn:
            conn.execute(sql)
    except Exception:
        pass  # Table might not exist in test setup


def get_token_count(db: DBUtility) -> int:
    """Get the count of tokens in the database."""
    from sqlalchemy import text
    
    sql = text("SELECT COUNT(*) as count FROM email_verification_tokens")
    
    try:
        with db.connect() as conn:
            result = conn.execute(sql).mappings().first()
            return result['count'] if result else 0
    except Exception:
        return 0


# =========================================================
# Account Helpers (for tests requiring accounts)
# =========================================================

def create_test_account(
    db: DBUtility,
    account_id: int = 1,
    email: str = "test@example.com",
    password: str = "hashed_password",
    fname: str = "Test",
    lname: str = "User",
    verified: bool = False
) -> int:
    """
    Create a test account in the database.
    Returns the account_id.
    """
    from sqlalchemy import text
    
    sql = text("""
        INSERT INTO account (id, email, password, fname, lname, verified)
        VALUES (:id, :email, :password, :fname, :lname, :verified)
        ON DUPLICATE KEY UPDATE
            email = VALUES(email),
            password = VALUES(password),
            fname = VALUES(fname),
            lname = VALUES(lname),
            verified = VALUES(verified)
    """)
    
    try:
        with db.transaction() as conn:
            conn.execute(sql, {
                "id": account_id,
                "email": email,
                "password": password,
                "fname": fname,
                "lname": lname,
                "verified": verified,
            })
        return account_id
    except Exception as e:
        raise RuntimeError(f"Failed to create test account: {e}")


def clear_accounts_table(db: DBUtility) -> None:
    """Clear all accounts from the table for clean test state."""
    from sqlalchemy import text
    
    # Disable foreign key checks temporarily to allow deletion
    try:
        with db.transaction() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.execute(text("DELETE FROM account"))
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    except Exception:
        pass  # Table might not exist in test setup

    
_CTX: Optional[IntegrationDBContext] = None
def get_db_instance() -> DBUtility:
    """
    Ensures docker DB is up and returns the initialized DBUtility singleton.
    """
    global _CTX
    if _CTX is None:
        _CTX = IntegrationDBContext.up()
    return _CTX.db
