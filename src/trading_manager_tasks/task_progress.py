"""Runtime task-progress files for dashboard-visible worker progress."""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_TASK_PROGRESS_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "task_progress"

STAGE_PROGRESS_CONTRACTS: dict[str, dict[str, str]] = {
    "data_acquisition": {
        "unit_label": "source-month requests",
        "progress_basis": "download/source partitions required by the six-month fold",
    },
    "feature_generation": {
        "unit_label": "feature months",
        "progress_basis": "feature partitions required by the six-month fold",
    },
    "model_generation": {
        "unit_label": "dataset months",
        "progress_basis": "chronological train/validation/test month coverage required by the six-month fold",
    },
    "model_training": {
        "unit_label": "training months",
        "progress_basis": "chronological training months used to fit a frozen model artifact for the six-month fold",
    },
    "replay": {
        "unit_label": "replay months",
        "progress_basis": "event replay months in the fixed five-year replay window",
    },
    "model_06_residual_event_governance": {
        "unit_label": "failure attributions",
        "progress_basis": "replay failure, residual, missed-opportunity, and path-deviation attribution units",
    },
    "model_evaluation": {
        "unit_label": "evaluation tests",
        "progress_basis": "required model-evaluation test checks",
    },
    "promotion_review": {
        "unit_label": "promotion tests",
        "progress_basis": "required promotion-readiness test checks",
    },
    "maintenance": {
        "unit_label": "data types",
        "progress_basis": "required maintenance handoff data kinds",
    },
}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def worker_progress_path(progress_root: Path, worker_id: str) -> Path:
    safe_worker_id = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in worker_id)
    return progress_root / f"{safe_worker_id or 'worker'}.json"


def _stage_type_from_stage_id(stage_id: object) -> str:
    text = str(stage_id or "")
    if ".model_training." in text:
        return "model_training"
    if ".model_generation." in text:
        return "model_generation"
    if "." in text:
        return text.rsplit(".", 1)[-1]
    if text.startswith("model_group."):
        return text.removeprefix("model_group.")
    return text


def progress_contract_for_stage(stage_id: object, *, fallback_unit_label: str = "items") -> dict[str, str]:
    """Return the dashboard progress unit contract for a manager stage."""

    stage_type = _stage_type_from_stage_id(stage_id)
    contract = STAGE_PROGRESS_CONTRACTS.get(stage_type)
    if contract is None:
        return {"unit_label": fallback_unit_label, "progress_basis": "explicit worker progress units"}
    return dict(contract)


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
        "progress_source": "active_progress_file",
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
        if "progress_basis" in extra:
            payload["progress_basis"] = extra["progress_basis"]
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
    return path


def write_task_progress_from_env(
    *,
    status: str = "running",
    unit_label: str | None = None,
    processed_count: int | None = None,
    expected_count: int | None = None,
    elapsed_seconds: float | None = None,
    expected_seconds: float | None = None,
    node_id: str | None = None,
    node_label: str | None = None,
    extra: Mapping[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Write active progress using the stage-executor environment contract."""

    source_env = env or os.environ
    progress_root_text = source_env.get("TRADING_MANAGER_TASK_PROGRESS_ROOT") or ""
    progress_root = Path(progress_root_text)
    worker_id = source_env.get("TRADING_MANAGER_TASK_PROGRESS_WORKER_ID") or ""
    task_uid = source_env.get("TRADING_MANAGER_TASK_PROGRESS_TASK_UID") or ""
    stage_id = source_env.get("TRADING_MANAGER_TASK_PROGRESS_STAGE_ID") or ""
    missing = [
        name
        for name, value in (
            ("TRADING_MANAGER_TASK_PROGRESS_ROOT", progress_root_text),
            ("TRADING_MANAGER_TASK_PROGRESS_WORKER_ID", worker_id),
            ("TRADING_MANAGER_TASK_PROGRESS_TASK_UID", task_uid),
            ("TRADING_MANAGER_TASK_PROGRESS_STAGE_ID", stage_id),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"missing task progress environment values: {', '.join(missing)}")
    contract = progress_contract_for_stage(stage_id)
    merged_extra: dict[str, Any] = {"progress_basis": contract["progress_basis"]}
    if extra:
        merged_extra.update(dict(extra))
    return write_task_progress_node(
        progress_root=progress_root,
        worker_id=worker_id,
        task_uid=task_uid,
        stage_id=stage_id,
        status=status,
        unit_label=unit_label or contract["unit_label"],
        processed_count=processed_count,
        expected_count=expected_count,
        elapsed_seconds=elapsed_seconds,
        expected_seconds=expected_seconds,
        node_id=node_id,
        node_label=node_label,
        extra=merged_extra,
    )


def clear_worker_task_progress(*, progress_root: Path, worker_id: str) -> None:
    """Clear a worker's previous active progress after the task reaches terminal state."""

    path = worker_progress_path(progress_root, worker_id)
    try:
        path.unlink()
    except FileNotFoundError:
        return


def _default_unit_label_for_stage(row: Mapping[str, Any], fallback: str) -> str:
    unit_label = row.get("unit_label")
    if unit_label:
        return str(unit_label)
    stage_id = str(row.get("stage_id") or "")
    if stage_id == "model_05_option_expression.option_chain_data_acquisition":
        return "option source"
    if stage_id.endswith(".data_acquisition"):
        if stage_id == "model_03_event_state.data_acquisition":
            return "event substrate"
    return progress_contract_for_stage(stage_id, fallback_unit_label=fallback)["unit_label"]


def _progress_basis_for_stage(row: Mapping[str, Any]) -> str | None:
    progress_basis = row.get("progress_basis")
    if progress_basis:
        return str(progress_basis)
    extra = row.get("extra")
    if isinstance(extra, Mapping) and extra.get("progress_basis"):
        return str(extra["progress_basis"])
    return progress_contract_for_stage(row.get("stage_id"), fallback_unit_label="items").get("progress_basis")


def _with_progress_contract(row: Mapping[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    payload.setdefault("progress_source", row.get("progress_source") or "active_progress_file")
    progress_basis = _progress_basis_for_stage(row)
    if progress_basis:
        payload.setdefault("progress_basis", progress_basis)
    return payload


def _progress_payload(row: Mapping[str, Any]) -> dict[str, Any] | None:
    expected = row.get("expected_count")
    processed = row.get("processed_count")
    elapsed = row.get("elapsed_seconds")
    expected_seconds = row.get("expected_seconds")
    try:
        expected_count = int(expected) if expected is not None else None
        ready_count = int(processed) if processed is not None else None
    except (TypeError, ValueError):
        expected_count = None
        ready_count = None
    if expected_count and ready_count is not None:
        ready = max(0, min(ready_count, expected_count))
        return _with_progress_contract(row, {
            "stage_id": row.get("stage_id"),
            "status": row.get("status") or "running",
            "unit_label": _default_unit_label_for_stage(row, "items"),
            "expected_count": expected_count,
            "ready_count": ready,
            "pending_count": max(expected_count - ready, 0),
            "failed_count": 0,
            "accepted_failed_count": 0,
            "can_unlock_downstream": ready >= expected_count,
        })
    try:
        expected_time = float(expected_seconds) if expected_seconds is not None else None
        elapsed_time = float(elapsed) if elapsed is not None else None
    except (TypeError, ValueError):
        expected_time = None
        elapsed_time = None
    if expected_time and elapsed_time is not None:
        elapsed_whole = max(0, min(int(elapsed_time), int(expected_time)))
        expected_whole = max(1, int(expected_time))
        return _with_progress_contract(row, {
            "stage_id": row.get("stage_id"),
            "status": row.get("status") or "running",
            "unit_label": _default_unit_label_for_stage(row, "seconds"),
            "expected_count": expected_whole,
            "ready_count": elapsed_whole,
            "pending_count": max(expected_whole - elapsed_whole, 0),
            "failed_count": 0,
            "accepted_failed_count": 0,
            "can_unlock_downstream": elapsed_whole >= expected_whole,
        })
    nodes = row.get("nodes")
    if isinstance(nodes, list) and nodes:
        node_rows = [node for node in nodes if isinstance(node, Mapping)]
        status_text = str(row.get("status") or "").lower()
        only_stage_start = (
            status_text == "running"
            and node_rows
            and all(str(node.get("node_id") or "") == "stage_started" for node in node_rows)
        )
        if only_stage_start:
            return _with_progress_contract(row, {
                "stage_id": row.get("stage_id"),
                "status": row.get("status") or "running",
                "unit_label": _default_unit_label_for_stage(row, "stage-step"),
                "expected_count": 1,
                "ready_count": 0,
                "pending_count": 1,
                "failed_count": 0,
                "accepted_failed_count": 0,
                "can_unlock_downstream": False,
                "progress_source": "active_progress_file",
            })
        meaningful_nodes = [
            node
            for node in node_rows
            if str(node.get("node_id") or "") != "stage_started"
            or node.get("processed_count") is not None
            or node.get("expected_count") is not None
            or node.get("elapsed_seconds") is not None
            or node.get("expected_seconds") is not None
            or str(node.get("status") or "").lower() in {"succeeded", "success", "completed", "complete", "ready", "failed", "error"}
        ]
        if not meaningful_nodes:
            return None
        node_rows = meaningful_nodes
        completed_nodes = [
            node
            for node in node_rows
            if str(node.get("status") or "").lower() in {"succeeded", "success", "completed", "complete", "ready"}
        ]
        failed_nodes = [node for node in node_rows if str(node.get("status") or "").lower() in {"failed", "error"}]
        expected_nodes = max(1, len(node_rows))
        ready_nodes = min(len(completed_nodes), expected_nodes)
        return _with_progress_contract(row, {
            "stage_id": row.get("stage_id"),
            "status": row.get("status") or "running",
            "unit_label": _default_unit_label_for_stage(row, "nodes"),
            "expected_count": expected_nodes,
            "ready_count": ready_nodes,
            "pending_count": max(expected_nodes - ready_nodes - len(failed_nodes), 0),
            "failed_count": len(failed_nodes),
            "accepted_failed_count": 0,
            "can_unlock_downstream": ready_nodes >= expected_nodes,
            "progress_source": "active_progress_file",
        })
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
        extra = payload.get("extra")
        if isinstance(extra, Mapping):
            progress["extra"] = dict(extra)
        rows[task_uid] = progress
    return rows


__all__ = [
    "DEFAULT_TASK_PROGRESS_ROOT",
    "clear_worker_task_progress",
    "load_active_task_progress",
    "progress_contract_for_stage",
    "worker_progress_path",
    "write_task_progress_from_env",
    "write_task_progress_node",
]
