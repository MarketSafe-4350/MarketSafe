# db_utility.py
from __future__ import annotations
from __future__ import annotations
from contextlib import contextmanager
from typing import  Iterator

from typing import  Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.exc import OperationalError

from server.src.utils import Validation, DatabaseUnavailableError


class DBUtility:
    """
    Simple DB utility with a connection pool.

    SQLAlchemy Engine == connection pool.
    Connections are borrowed from the pool and returned when closed.

    Pass this DBUtility instance to your Manager/Repository classes.
    """
    _instance: Optional["DBUtility"] = None  # class-level singleton holder

    @staticmethod
    def initialize(
            *,
            host: str,
            port: int,
            database: str,
            username: str,
            password: str,
            pool_size: int = 5,
            max_overflow: int = 10,
            pool_timeout: int = 30,
            pool_recycle: int = 1800,
            pool_pre_ping: bool = True,
            driver: str = "mysql+pymysql",
    ) -> None:
        """
        Initializes the singleton instance.
        Must be called once at application startup.
        """
        if DBUtility._instance is not None:
            raise RuntimeError("DBUtility is already initialized")

        DBUtility._instance = DBUtility(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            driver=driver,
        )

    def __init__(
        self,
        *,
        host: str,            # e.g. "127.0.0.1" or "db" (docker service name)
        port: int,            # e.g. 3306
        database: str,        # e.g. "marketplace"
        username: str,        # e.g. "root"
        password: str,        # e.g. "pass"
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
        driver="mysql+pymysql"

    ):
        # ---- validate required inputs (fail fast) ----
        Validation.require_str(host, "host")
        Validation.require_int(port, "port")
        Validation.require_str(database, "database")
        Validation.require_str(username, "username")
        Validation.require_not_none(password, "password")

        url = f"{driver}://{username}:{password}@{host}:{port}/{database}"

        self._engine: Engine = create_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            future=True,
        )

        # -----------------------------
        # Request-time behavior
        # -----------------------------

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        """
        Borrow a connection from the pool.
        If DB is down, raises DatabaseUnavailableError (to be mapped to 503).
        """
        try:
            with self._engine.connect() as conn:
                yield conn
        except OperationalError as e:
            raise DatabaseUnavailableError("Database is unavailable.") from e

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        """
        Transaction wrapper.
        If DB is down, raises DatabaseUnavailableError (to be mapped to 503).
        """
        try:
            with self._engine.begin() as conn:
                yield conn
        except OperationalError as e:
            raise DatabaseUnavailableError("Database is unavailable.") from e

    @property
    def engine(self) -> Engine:
        """Expose the underlying Engine (pool) if you want to share it."""
        return self._engine

    def dispose(self) -> None:
        """Close all pooled connections (useful on app shutdown)."""
        self._engine.dispose()
