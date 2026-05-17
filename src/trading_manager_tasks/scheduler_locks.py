"""Scheduler lock contract helpers.

The daemon may have one process-level lock, but historical work needs narrower
contract keys before provider concurrency expands. These helpers define stable
lock identities and provide local file-backed acquisition without starting
services, dispatching providers, or mutating workflow state by themselves.
"""

from __future__ import annotations

import json
import os
import re
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Literal

DEFAULT_STORAGE_ROOT = Path("storage")
DEFAULT_RUNTIME_DIR = DEFAULT_STORAGE_ROOT / "runtime"
DEFAULT_DAEMON_LOCK_PATH = DEFAULT_RUNTIME_DIR / "historical_scheduler.lock"
DEFAULT_LOCKS_DIR = DEFAULT_RUNTIME_DIR / "locks"

SchedulerLockScope = Literal["daemon", "month_stage", "provider_partition", "reconcile", "promotion"]
_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
_SAFE_TOKEN_RE = re.compile(r"[^A-Za-z0-9_.=-]+")


@dataclass(frozen=True)
class SchedulerLockRef:
    """Machine-readable lock identity for historical scheduler coordination."""

    contract_type: str
    lock_scope: SchedulerLockScope
    lock_key: str
    lock_path: str
    month: str | None = None
    stage_id: str | None = None
    provider_id: str | None = None
    partition_id: str | None = None
    model_id: str | None = None
    candidate_ref: str | None = None

    def summary_row(self) -> dict[str, str | None]:
        return asdict(self)


def _require(value: str | None, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def _require_month(month: str) -> str:
    text = _require(month, "month")
    if not _MONTH_RE.match(text):
        raise ValueError("month must use YYYY-MM")
    month_number = int(text.split("-", 1)[1])
    if month_number < 1 or month_number > 12:
        raise ValueError("month must use YYYY-MM with month 01-12")
    return text


def lock_token(value: str) -> str:
    """Return a filesystem-safe token that preserves readable ids."""

    text = _require(value, "lock token")
    token = _SAFE_TOKEN_RE.sub("_", text).strip("._-")
    return token[:120] or "lock"


def daemon_lock_ref(lock_path: Path = DEFAULT_DAEMON_LOCK_PATH) -> SchedulerLockRef:
    """Return the process-level single-daemon lock contract."""

    return SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="daemon",
        lock_key="lock:daemon:historical_scheduler",
        lock_path=str(lock_path),
    )


def month_stage_lock_ref(month: str, stage_id: str, *, locks_dir: Path = DEFAULT_LOCKS_DIR) -> SchedulerLockRef:
    """Return the lock that protects one month/stage workflow transition lane."""

    month = _require_month(month)
    stage_id = _require(stage_id, "stage_id")
    path = locks_dir / "stage" / month / f"{lock_token(stage_id)}.lock"
    return SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="month_stage",
        lock_key=f"lock:stage:{month}:{stage_id}",
        lock_path=str(path),
        month=month,
        stage_id=stage_id,
    )


def provider_partition_lock_ref(
    month: str,
    stage_id: str,
    provider_id: str,
    partition_id: str,
    *,
    locks_dir: Path = DEFAULT_LOCKS_DIR,
) -> SchedulerLockRef:
    """Return the lock for one provider worker partition.

    Provider workers may run concurrently only when their partition lock keys are
    distinct. They still must not directly advance terminal workflow state; a
    reconcile lock owns that transition.
    """

    month = _require_month(month)
    stage_id = _require(stage_id, "stage_id")
    provider_id = _require(provider_id, "provider_id")
    partition_id = _require(partition_id, "partition_id")
    path = locks_dir / "provider" / month / lock_token(stage_id) / lock_token(provider_id) / f"{lock_token(partition_id)}.lock"
    return SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="provider_partition",
        lock_key=f"lock:provider:{month}:{stage_id}:{provider_id}:{partition_id}",
        lock_path=str(path),
        month=month,
        stage_id=stage_id,
        provider_id=provider_id,
        partition_id=partition_id,
    )


def reconcile_lock_ref(month: str, stage_id: str, *, locks_dir: Path = DEFAULT_LOCKS_DIR) -> SchedulerLockRef:
    """Return the lock for reconciling provider receipts into stage state."""

    month = _require_month(month)
    stage_id = _require(stage_id, "stage_id")
    path = locks_dir / "reconcile" / month / f"{lock_token(stage_id)}.lock"
    return SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="reconcile",
        lock_key=f"lock:reconcile:{month}:{stage_id}",
        lock_path=str(path),
        month=month,
        stage_id=stage_id,
    )


def promotion_lock_ref(model_id: str, candidate_ref: str, *, locks_dir: Path = DEFAULT_LOCKS_DIR) -> SchedulerLockRef:
    """Return the lock for one model-promotion candidate review lane."""

    model_id = _require(model_id, "model_id")
    candidate_ref = _require(candidate_ref, "candidate_ref")
    path = locks_dir / "promotion" / lock_token(model_id) / f"{lock_token(candidate_ref)}.lock"
    return SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:promotion:{model_id}:{candidate_ref}",
        lock_path=str(path),
        model_id=model_id,
        candidate_ref=candidate_ref,
    )


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def acquire_scheduler_lock(ref: SchedulerLockRef, *, stale_after_seconds: int = 6 * 60 * 60) -> Iterator[SchedulerLockRef]:
    """Acquire one filesystem scheduler lock for a narrow work lane.

    The lock is intentionally local and file-backed so clean environments can
    exercise concurrency guards without a database or service. If a recorded PID
    is dead, the stale lock is replaced immediately; malformed locks are replaced
    only after ``stale_after_seconds``.
    """

    path = Path(ref.lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "contract_type": ref.contract_type,
        "lock_scope": ref.lock_scope,
        "lock_key": ref.lock_key,
        "pid": os.getpid(),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    acquired = False
    try:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError as exc:
            existing_text = path.read_text(encoding="utf-8") if path.exists() else "{}"
            try:
                existing = json.loads(existing_text)
            except json.JSONDecodeError:
                existing = {}
            existing_pid = int(existing.get("pid") or 0)
            age = time.time() - path.stat().st_mtime if path.exists() else 0
            if existing_pid > 0:
                if _process_exists(existing_pid):
                    raise RuntimeError(f"scheduler lock is active: {ref.lock_key} at {path}") from exc
            elif age < stale_after_seconds:
                raise RuntimeError(f"scheduler lock is active: {ref.lock_key} at {path}") from exc
            path.unlink(missing_ok=True)
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.write("\n")
        acquired = True
        yield ref
    finally:
        if acquired:
            path.unlink(missing_ok=True)


def scheduler_lock_plan(
    *,
    month: str | None,
    selected_work: str | None,
    next_internal_stage: str | None,
    locks_dir: Path = DEFAULT_LOCKS_DIR,
    daemon_lock_path: Path = DEFAULT_DAEMON_LOCK_PATH,
) -> dict[str, Any]:
    """Return read-only lock requirements for the selected scheduler work.

    This is a planning/status surface only. It does not acquire locks, start
    workers, dispatch providers, or advance workflow state.
    """

    lock_refs: list[dict[str, str | None]] = [daemon_lock_ref(daemon_lock_path).summary_row()]
    templates: list[dict[str, str]] = []
    scopes = ["daemon"]
    if month and selected_work:
        if next_internal_stage == "chronological_month_advance":
            stage_ref = month_stage_lock_ref(month, "chronological_month_advance", locks_dir=locks_dir)
            lock_refs.append(stage_ref.summary_row())
            scopes.append("month_stage")
        elif selected_work.startswith("layer_"):
            stage_ref = month_stage_lock_ref(month, selected_work, locks_dir=locks_dir)
            lock_refs.append(stage_ref.summary_row())
            scopes.append("month_stage")
            if next_internal_stage == "autonomous_historical_provider_acquisition":
                reconcile_ref = reconcile_lock_ref(month, selected_work, locks_dir=locks_dir)
                lock_refs.append(reconcile_ref.summary_row())
                scopes.append("reconcile")
                templates.append(
                    {
                        "lock_scope": "provider_partition",
                        "lock_key_template": f"lock:provider:{month}:{selected_work}:<provider_id>:<partition_id>",
                        "lock_path_template": str(locks_dir / "provider" / month / lock_token(selected_work) / "<provider_id>" / "<partition_id>.lock"),
                    }
                )
                scopes.append("provider_partition")
    return {
        "contract_type": "scheduler_lock_plan",
        "lock_contract_type": "scheduler_lock",
        "selected_work": selected_work,
        "next_internal_stage": next_internal_stage,
        "required_lock_scopes": sorted(set(scopes), key=scopes.index),
        "lock_refs": lock_refs,
        "lock_templates": templates,
        "mutation_performed": False,
    }


__all__ = [
    "DEFAULT_DAEMON_LOCK_PATH",
    "DEFAULT_LOCKS_DIR",
    "SchedulerLockRef",
    "acquire_scheduler_lock",
    "daemon_lock_ref",
    "lock_token",
    "month_stage_lock_ref",
    "promotion_lock_ref",
    "provider_partition_lock_ref",
    "reconcile_lock_ref",
    "scheduler_lock_plan",
]
