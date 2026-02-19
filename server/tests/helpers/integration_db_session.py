from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Optional

from src.db import DBUtility
from .integration_db import IntegrationDBContext

_lock = threading.Lock()
_ctx: Optional[IntegrationDBContext] = None
_refcount: int = 0
_suite_owner: bool = False  # if True, suite will close; classes won't


@dataclass(frozen=True)
class SessionHandle:
    """Returned to callers so they can release safely."""
    started_by_caller: bool


def suite_begin(timeout_s: int = 60) -> None:
    """
    Called by the integration suite entrypoint.
    Ensures DB is up once and marks suite ownership so test classes won't down().
    """
    global _ctx, _suite_owner
    with _lock:
        if _ctx is None:
            _ctx = IntegrationDBContext.up(timeout_s=timeout_s)
        _suite_owner = True


def suite_end(remove_volumes: bool = True) -> None:
    """
    Called by the integration suite entrypoint.
    Brings DB down regardless of refcount (because suite owns lifecycle).
    """
    global _ctx, _refcount, _suite_owner
    with _lock:
        if _ctx is not None:
            _ctx.down(remove_volumes=remove_volumes)
        _ctx = None
        _refcount = 0
        _suite_owner = False


def acquire(timeout_s: int = 60) -> SessionHandle:
    """
    Called by test classes in setUpClass.
    Starts DB if needed and increments refcount unless suite owns lifecycle.
    """
    global _ctx, _refcount

    with _lock:
        if _ctx is None:
            _ctx = IntegrationDBContext.up(timeout_s=timeout_s)

        if _suite_owner:
            # suite will handle shutdown; no refcount needed
            return SessionHandle(started_by_caller=False)

        _refcount += 1
        return SessionHandle(started_by_caller=True)


def get_db():
    """Access the live DB client/engine created by IntegrationDBContext."""
    with _lock:
        if _ctx is None:
            raise RuntimeError("Integration DB session not started. Call acquire() first.")
        return _ctx.db  # assumes your context exposes .db


def release(handle: SessionHandle, remove_volumes: bool = True) -> None:
    """
    Called by test classes in tearDownClass.
    Decrements refcount and stops DB when it reaches 0 (unless suite owns lifecycle).
    """
    global _ctx, _refcount

    with _lock:
        if _suite_owner:
            return  # suite will close it

        if not handle.started_by_caller:
            return

        _refcount = max(0, _refcount - 1)
        if _refcount == 0 and _ctx is not None:
            # Dispose DB pool so we don't keep stale/broken connections
            try:
                DBUtility.instance().dispose()
                DBUtility.reset()
            except Exception:
                pass

            _ctx.down(remove_volumes=remove_volumes)
            _ctx = None
