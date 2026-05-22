"""Runtime task-progress files for dashboard-visible worker progress."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_TASK_PROGRESS_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "task_progress"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def worker_progress_path(progress_root: Path, worker_id: str) -> Path:
    safe_worker_id = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in worker_id)
    return progress_root / f"{safe_worker_id or 'worker'}.json"


def write_task_progress_node(
    *,
    progress_root: Path,
    worker_id: str,
    task_uid: str,
    stage_id: str,
    status: str = "running",
    unit_label: str | None = None,
    processed_count: int | None = None,
    expected_count: int | None = None,
    elapsed_seconds: float | None = None,
    expected_seconds: float | None = None,
    node_id: str | None = None,
    node_label: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> Path:
    """Write or replace one worker's active task-progress file."""

    progress_root.mkdir(parents=True, exist_ok=True)
    path = worker_progress_path(progress_root, worker_id)
    now = utc_now_iso()
    payload: dict[str, Any] = {
        "contract_type": "manager_worker_task_progress",
        "worker_id": worker_id,
        "task_uid": task_uid,
        "stage_id": stage_id,
        "status": status,
        "unit_label": unit_label,
        "processed_count": processed_count,
        "expected_count": expected_count,
        "elapsed_seconds": elapsed_seconds,
        "expected_seconds": expected_seconds,
        "updated_at_utc": now,
        "nodes": [
            {
                "node_id": node_id or stage_id,
                "node_label": node_label or stage_id,
                "status": status,
                "processed_count": processed_count,
                "expected_count": expected_count,
                "elapsed_seconds": elapsed_seconds,
                "expected_seconds": expected_seconds,
                "updated_at_utc": now,
            }
        ],
    }
    if extra:
        payload["extra"] = dict(extra)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def clear_worker_task_progress(*, progress_root: Path, worker_id: str) -> None:
    """Clear a worker's previous active progress after the task reaches terminal state."""

    path = worker_progress_path(progress_root, worker_id)
    try:
        path.unlink()
    except FileNotFoundError:
        return


def _progress_payload(row: Mapping[str, Any]) -> dict[str, Any] | None:
    expected = row.get("expected_count")
    processed = row.get("processed_count")
    elapsed = row.get("elapsed_seconds")
    expected_seconds = row.get("expected_seconds")
    unit_label = row.get("unit_label")
    try:
        expected_count = int(expected) if expected is not None else None
        ready_count = int(processed) if processed is not None else None
    except (TypeError, ValueError):
        expected_count = None
        ready_count = None
    if expected_count and ready_count is not None:
        ready = max(0, min(ready_count, expected_count))
        return {
            "stage_id": row.get("stage_id"),
            "status": row.get("status") or "running",
            "unit_label": str(unit_label or "items"),
            "expected_count": expected_count,
            "ready_count": ready,
            "pending_count": max(expected_count - ready, 0),
            "failed_count": 0,
            "accepted_failed_count": 0,
            "can_unlock_downstream": ready >= expected_count,
        }
    try:
        expected_time = float(expected_seconds) if expected_seconds is not None else None
        elapsed_time = float(elapsed) if elapsed is not None else None
    except (TypeError, ValueError):
        expected_time = None
        elapsed_time = None
    if expected_time and elapsed_time is not None:
        elapsed_whole = max(0, min(int(elapsed_time), int(expected_time)))
        expected_whole = max(1, int(expected_time))
        return {
            "stage_id": row.get("stage_id"),
            "status": row.get("status") or "running",
            "unit_label": str(unit_label or "seconds"),
            "expected_count": expected_whole,
            "ready_count": elapsed_whole,
            "pending_count": max(expected_whole - elapsed_whole, 0),
            "failed_count": 0,
            "accepted_failed_count": 0,
            "can_unlock_downstream": elapsed_whole >= expected_whole,
        }
    nodes = row.get("nodes")
    if isinstance(nodes, list) and nodes:
        return {
            "stage_id": row.get("stage_id"),
            "status": row.get("status") or "running",
            "unit_label": str(unit_label or "nodes"),
            "expected_count": None,
            "ready_count": None,
            "pending_count": None,
            "failed_count": 0,
            "accepted_failed_count": 0,
            "can_unlock_downstream": False,
        }
    return None


def load_active_task_progress(progress_root: Path) -> dict[str, dict[str, Any]]:
    """Return active progress payloads keyed by task uid."""

    if not progress_root.exists():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(progress_root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        task_uid = str(payload.get("task_uid") or "")
        if not task_uid:
            continue
        progress = _progress_payload(payload)
        if progress is None:
            continue
        progress["worker_id"] = payload.get("worker_id")
        progress["updated_at_utc"] = payload.get("updated_at_utc")
        nodes = payload.get("nodes")
        if isinstance(nodes, list):
            progress["nodes"] = nodes
        rows[task_uid] = progress
    return rows


__all__ = [
    "DEFAULT_TASK_PROGRESS_ROOT",
    "clear_worker_task_progress",
    "load_active_task_progress",
    "worker_progress_path",
    "write_task_progress_node",
]
