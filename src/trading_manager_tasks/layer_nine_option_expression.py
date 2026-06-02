"""Layer 9 option-expression gate review helpers.

This module is deliberately no-provider. It reviews completed Layer 8
underlying-action rows for option-expression-worthy actions before ThetaData
option-snapshot acquisition is prepared for the Layer 9 trading-guidance
boundary. If the month has no active underlying action chain, the correct
``layer_09_option_expression`` acquisition outcome is a reviewed no-provider skip,
not an empty provider request.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError, fetch_manager_requests, persist_manager_requests
from .provider_dispatch import ProviderDispatchItem, ProviderDispatchSummary, select_provider_worker_count
from .request_payloads import DEFAULT_STORAGE_ROOT
from .storage_paths import data_storage_root

DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_OUTPUT_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "layer_09_option_expression" / "gate_review"
DEFAULT_SOURCE_OUTPUT_ROOT = data_storage_root() / "layer_09_option_expression" / "source_05_option_expression"
DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
STAGE_ID = "layer_09_option_expression.data_acquisition"
SOURCE_ID = "m09_option_expression_data_acquisition"
TARGET_COMPONENT_ID = "source_05_option_expression"
OPTION_BUCKET_POLICY_REF = "LAYER_09_OPTION_BUCKET_STRIKE_POLICY"
DEFAULT_OPTION_SNAPSHOT_MAX_DTE = 45
DEFAULT_OPTION_SNAPSHOT_STRIKE_RANGE = 5
ACTIVE_ACTION_TYPES = {
    "increase_long",
    "decrease_long",
    "open_long",
    "open_short",
    "increase_short",
    "decrease_short",
    "bearish_underlying_path_but_no_short_allowed",
}
INACTIVE_ACTION_TYPES = {"", "none", "no_trade", "maintain"}
INACTIVE_ACTION_SIDES = {"", "none", "neutral"}


@dataclass(frozen=True)
class LayerNineRequestPreview:
    """A bounded preview of a future option-chain snapshot request."""

    request_id: str
    target_candidate_id: str
    underlying: str | None
    snapshot_time: str
    underlying_action_plan_ref: str | None
    action_type: str
    action_side: str
    dominant_horizon: str | None
    action_confidence_score: float | None
    provider: str = "thetadata"
    target_component_id: str = TARGET_COMPONENT_ID
    snapshot_type: str = "entry"
    max_dte: int = DEFAULT_OPTION_SNAPSHOT_MAX_DTE
    strike_range: int = DEFAULT_OPTION_SNAPSHOT_STRIKE_RANGE
    option_bucket_policy_ref: str = OPTION_BUCKET_POLICY_REF

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["source_task_key"] = {
            "task_id": self.request_id,
            "source": SOURCE_ID,
            "params": {
                "underlying": self.underlying,
                "snapshot_time": self.snapshot_time,
                "snapshot_type": self.snapshot_type,
                "max_dte": self.max_dte,
                "strike_range": self.strike_range,
                "option_bucket_policy_ref": self.option_bucket_policy_ref,
            },
        }
        return row


@dataclass(frozen=True)
class LayerNineGateReview:
    """No-provider review of whether Layer 9 needs option-snapshot acquisition."""

    contract_type: str
    stage_id: str
    start_month: str
    end_month: str
    status: str
    reviewed_decision: str
    total_layer_8_rows: int
    active_target_chain_count: int
    active_request_count: int
    request_previews: tuple[LayerNineRequestPreview, ...]
    evidence_refs: tuple[str, ...]
    reason: str
    recommended_next_action: str
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["request_previews"] = [item.summary_row() for item in self.request_previews]
        row["evidence_refs"] = list(self.evidence_refs)
        return row


def _database_url(explicit: str | None) -> str:
    if explicit:
        return explicit
    if os.environ.get("OPENCLAW_DATABASE_URL"):
        return os.environ["OPENCLAW_DATABASE_URL"]
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    raise TaskSystemError(f"database URL not supplied and {DEFAULT_DB_URL_FILE} does not exist")


def _month_start(month: str) -> str:
    return f"{month}-01T00:00:00-05:00"


def _exclusive_month_start(month: str) -> str:
    year = int(month[:4])
    month_number = int(month[5:])
    if month_number == 12:
        year += 1
        month_number = 1
    else:
        month_number += 1
    return f"{year:04d}-{month_number:02d}-01T00:00:00-05:00"


def _safe_token(value: str) -> str:
    return "_".join(part for part in "".join(char.lower() if char.isalnum() else "_" for char in value).split("_") if part)


def _short_target(target_candidate_id: str) -> str:
    token = _safe_token(target_candidate_id)
    return token[-16:] if len(token) > 16 else token


def _request_id(row: Mapping[str, Any], *, start_month: str) -> str:
    underlying = str(row.get("underlying") or "unknown").lower()
    snapshot = _safe_token(str(row.get("snapshot_time") or row.get("tradeable_time") or row.get("available_time") or "unknown"))
    target = _short_target(str(row.get("target_candidate_id") or "target"))
    return f"mgrreq_layer9_option_snapshot_{underlying}_{start_month.replace('-', '_')}_{snapshot}_{target}"


def _task_key_path_for_request(request_id: str, *, start_month: str, storage_root: Path = DEFAULT_STORAGE_ROOT) -> Path:
    return storage_root / "runtime" / "layer_09_option_expression" / "source_05_option_expression" / start_month / request_id / "task_key.json"


def _task_key_ref_for_request(request_id: str, *, start_month: str) -> str:
    return f"storage://trading-manager/runtime/layer_09_option_expression/source_05_option_expression/{start_month}/{request_id}/task_key.json"


def _source_output_root_for_request(request_id: str, *, start_month: str, source_output_root: Path = DEFAULT_SOURCE_OUTPUT_ROOT) -> Path:
    return source_output_root / start_month / request_id


def _is_active_layer_8_row(row: Mapping[str, Any]) -> bool:
    action_type = str(row.get("action_type") or "").strip().lower()
    action_side = str(row.get("action_side") or "").strip().lower()
    if action_type in INACTIVE_ACTION_TYPES:
        return False
    if action_side in INACTIVE_ACTION_SIDES and action_type not in ACTIVE_ACTION_TYPES:
        return False
    return True


def request_previews_from_layer_8_rows(rows: Iterable[Mapping[str, Any]], *, start_month: str) -> tuple[LayerNineRequestPreview, ...]:
    """Build future ThetaData request previews from active Layer 8 rows only."""

    previews: list[LayerNineRequestPreview] = []
    seen: set[str] = set()
    for row in rows:
        if not _is_active_layer_8_row(row):
            continue
        request_id = _request_id(row, start_month=start_month)
        if request_id in seen:
            continue
        seen.add(request_id)
        previews.append(
            LayerNineRequestPreview(
                request_id=request_id,
                target_candidate_id=str(row.get("target_candidate_id") or ""),
                underlying=str(row.get("underlying")) if row.get("underlying") else None,
                snapshot_time=str(row.get("snapshot_time") or row.get("tradeable_time") or row.get("available_time") or ""),
                underlying_action_plan_ref=str(row.get("underlying_action_plan_ref")) if row.get("underlying_action_plan_ref") else None,
                action_type=str(row.get("action_type") or ""),
                action_side=str(row.get("action_side") or ""),
                dominant_horizon=str(row.get("dominant_horizon")) if row.get("dominant_horizon") else None,
                action_confidence_score=float(row["action_confidence_score"]) if row.get("action_confidence_score") is not None else None,
            )
        )
    return tuple(previews)


def build_layer_nine_gate_review(
    *,
    start_month: str,
    end_month: str,
    layer_8_rows: Sequence[Mapping[str, Any]],
    evidence_refs: Sequence[str] = (),
) -> LayerNineGateReview:
    previews = request_previews_from_layer_8_rows(layer_8_rows, start_month=start_month)
    if previews:
        status = "provider_acquisition_ready"
        reviewed_decision = "active_target_chain_ready_for_autonomous_option_acquisition"
        reason = f"{len(previews)} active Layer 8 target-chain rows are ready for autonomous ThetaData option snapshot acquisition before Layer 9 guidance/option-expression review."
        recommended_next_action = "prepare_option_expression_acquisition"
    else:
        status = "no_provider_skip_accepted"
        reviewed_decision = "accepted_skip_no_active_target_chain"
        reason = "Layer 8 produced no active underlying-action chain for Layer 9 option-expression review; all rows are no-trade/maintain/neutral, so no option-chain provider call is warranted for this month."
        recommended_next_action = "record_layer_09_data_acquisition_no_provider_skip"
    return LayerNineGateReview(
        contract_type="manager_layer_09_option_expression_gate_review",
        stage_id=STAGE_ID,
        start_month=start_month,
        end_month=end_month,
        status=status,
        reviewed_decision=reviewed_decision,
        total_layer_8_rows=len(layer_8_rows),
        active_target_chain_count=len(previews),
        active_request_count=len(previews),
        request_previews=previews,
        evidence_refs=tuple(evidence_refs),
        reason=reason,
        recommended_next_action=recommended_next_action,
    )


def fetch_layer_8_rows(*, database_url: str, start_month: str, end_month: str) -> list[dict[str, Any]]:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    start = _month_start(start_month)
    end = _exclusive_month_start(end_month)
    query = """
        WITH l8_rows AS MATERIALIZED (
          SELECT
            l8.available_time,
            l8.tradeable_time,
            l8.target_candidate_id,
            COALESCE(l8.tradeable_time, l8.available_time) AS snapshot_time,
            l8.underlying_action_plan_ref,
            l8."8_resolved_underlying_action_type" AS action_type,
            l8."8_resolved_action_side" AS action_side,
            l8."8_resolved_dominant_horizon" AS dominant_horizon,
            l8."8_resolved_action_confidence_score" AS action_confidence_score
          FROM trading_model.model_08_underlying_action l8
          WHERE l8.available_time::timestamptz >= %s::timestamptz
            AND l8.available_time::timestamptz < %s::timestamptz
        ),
        target_symbols AS (
          SELECT DISTINCT ON (target_candidate_id)
            source.target_candidate_id,
            source.symbol AS underlying
          FROM trading_data.source_03_target_state source
          JOIN (SELECT DISTINCT target_candidate_id FROM l8_rows) ids USING (target_candidate_id)
          ORDER BY source.target_candidate_id, source.available_time ASC
        )
        SELECT
          l8_rows.available_time,
          l8_rows.tradeable_time,
          l8_rows.target_candidate_id,
          ts.underlying,
          l8_rows.snapshot_time,
          l8_rows.underlying_action_plan_ref,
          l8_rows.action_type,
          l8_rows.action_side,
          l8_rows.dominant_horizon,
          l8_rows.action_confidence_score
        FROM l8_rows
        LEFT JOIN target_symbols ts USING (target_candidate_id)
        ORDER BY l8_rows.available_time::timestamptz ASC, l8_rows.target_candidate_id ASC
    """
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '5min'")
            cursor.execute(query, (start, end))
            return [dict(row) for row in cursor.fetchall()]


def write_gate_review_artifacts(review: LayerNineGateReview, *, output_root: Path = DEFAULT_OUTPUT_ROOT) -> tuple[Path, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    review_path = output_root / f"layer_09_option_expression_gate_review_{review.start_month}.json"
    receipt_path = output_root / f"layer_09_option_expression_gate_review_receipt_{review.start_month}.json"
    review_payload = review.summary_row()
    review_payload["evidence_refs"] = [*review_payload["evidence_refs"], str(review_path), str(receipt_path)]
    review_path.write_text(json.dumps(review_payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    receipt_status = "succeeded" if review.status in {"no_provider_skip_accepted", "provider_acquisition_ready"} else "blocked"
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = {
        "contract_type": "component_completion_receipt",
        "manager_stage_id": review.stage_id,
        "stage_type": "data_acquisition",
        "status": receipt_status,
        "started_at": now,
        "completed_at": now,
        "runs": [
            {
                "run_id": f"layer_09_option_expression_gate_review_{review.start_month}",
                "status": receipt_status,
                "output_refs": [str(review_path)],
                "row_counts": {
                    "layer_8_rows_reviewed": review.total_layer_8_rows,
                    "active_layer_8_request_candidates": review.active_request_count,
                },
            }
        ],
        "provider_calls": 0,
        "dispatch_performed": False,
        "model_activation_performed": False,
        "broker_execution_performed": False,
        "storage_lifecycle_mutation_performed": False,
        "reason": review.reason,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return review_path, receipt_path


def manager_requests_from_gate_review(
    review: LayerNineGateReview,
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    source_output_root: Path = DEFAULT_SOURCE_OUTPUT_ROOT,
) -> tuple[dict[str, Any], ...]:
    """Build manager_request rows for reviewed Layer 9 option snapshot acquisition."""

    requests: list[dict[str, Any]] = []
    for preview in review.request_previews:
        task_key_path = _task_key_path_for_request(preview.request_id, start_month=review.start_month, storage_root=storage_root)
        task_key = preview.summary_row()["source_task_key"]
        task_key.update(
            {
                "output_root": str(_source_output_root_for_request(preview.request_id, start_month=review.start_month, source_output_root=source_output_root)),
                "manager_controls": {
                    "allow_live_provider_calls": True,
                    "autonomous_historical_provider_acquisition": True,
                    "stage_id": STAGE_ID,
                    "start_month": review.start_month,
                    "end_month": review.end_month,
                },
                "policy_refs": ["autonomous_historical_provider_acquisition", "layer_09_option_expression_source_acquisition"],
            }
        )
        requests.append(
            {
                "request_id": preview.request_id,
                "contract_type": "manager_request",
                "request_kind": "option_snapshot",
                "status": "requested",
                "requested_by": "trading-manager.layer_09_option_expression",
                "target_component_id": TARGET_COMPONENT_ID,
                "target_component_kind": "data_source",
                "target_repo_id": "trading-data",
                "expected_outputs": ["trading_data.m09_option_expression_data_acquisition"],
                "policy_refs": ["autonomous_historical_provider_acquisition", "layer_09_option_expression_source_acquisition"],
                "priority": "normal",
                "deadline_at_utc": None,
                "parameter_ref": _task_key_ref_for_request(preview.request_id, start_month=review.start_month),
                "dry_run": False,
                "symbol": preview.underlying,
                "month": review.start_month,
                "_task_key_path": str(task_key_path),
                "_task_key": task_key,
            }
        )
    return tuple(requests)


def write_layer_nine_task_keys(requests: Sequence[Mapping[str, Any]]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for request in requests:
        path = Path(str(request["_task_key_path"]))
        task_key = dict(request["_task_key"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return tuple(paths)


def prepare_layer_nine_option_acquisition(
    *,
    start_month: str,
    end_month: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    source_output_root: Path = DEFAULT_SOURCE_OUTPUT_ROOT,
    write: bool = False,
    persist_sql: bool = False,
    database_url: str | None = None,
) -> tuple[LayerNineGateReview, tuple[dict[str, Any], ...], tuple[Path, ...]]:
    """Review Layer 8 rows and prepare current Layer 9 source acquisition requests."""

    rows = fetch_layer_8_rows(database_url=_database_url(database_url), start_month=start_month, end_month=end_month)
    review = build_layer_nine_gate_review(
        start_month=start_month,
        end_month=end_month,
        layer_8_rows=rows,
        evidence_refs=("sql:trading_model.model_08_underlying_action", "sql:trading_data.source_03_target_state"),
    )
    if write:
        review_path, receipt_path = write_gate_review_artifacts(review, output_root=output_root)
        review = LayerNineGateReview(
            **{
                **review.summary_row(),
                "request_previews": review.request_previews,
                "evidence_refs": (*review.evidence_refs, str(review_path), str(receipt_path)),
            }
        )
    requests = manager_requests_from_gate_review(review, storage_root=storage_root, source_output_root=source_output_root)
    task_key_paths: tuple[Path, ...] = ()
    if write and requests:
        task_key_paths = write_layer_nine_task_keys(requests)
    if persist_sql and requests:
        persistable = [{key: value for key, value in request.items() if not key.startswith("_")} for request in requests]
        persist_manager_requests(persistable, database_url=database_url)
    return review, requests, task_key_paths


def _matches_layer_nine_request(row: Mapping[str, Any], *, start_month: str, end_month: str) -> bool:
    if row.get("target_component_id") != TARGET_COMPONENT_ID:
        return False
    if row.get("request_kind") != "option_snapshot":
        return False
    text = " ".join(str(row.get(key) or "") for key in ("request_id", "parameter_ref"))
    return start_month in text or end_month in text


def _layer_nine_request_rows(
    *,
    start_month: str,
    end_month: str,
    request_ids: Sequence[str] = (),
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    request_filter = {item.strip() for item in request_ids if item.strip()}
    rows = [
        dict(row)
        for row in fetch_manager_requests(database_url=database_url)
        if _matches_layer_nine_request(row, start_month=start_month, end_month=end_month)
    ]
    if request_filter:
        rows = [row for row in rows if str(row.get("request_id") or "") in request_filter]
        found = {str(row.get("request_id") or "") for row in rows}
        missing = sorted(request_filter - found)
        if missing:
            raise TaskSystemError("requested Layer 9 option request ids are not available: " + ",".join(missing))
    if not rows:
        raise TaskSystemError("no Layer 9 option snapshot requests available for dispatch")
    return sorted(rows, key=lambda row: str(row.get("request_id") or ""))


def _runtime_task_key(task_key: Mapping[str, Any]) -> dict[str, Any]:
    runtime_key = dict(task_key)
    runtime_key["dry_run"] = False
    controls = dict(runtime_key.get("manager_controls") or {})
    controls["allow_live_provider_calls"] = True
    controls["autonomous_historical_provider_acquisition"] = True
    runtime_key["manager_controls"] = controls
    params = dict(runtime_key.get("params") or {})
    params["manager_dry_run"] = False
    runtime_key["params"] = params
    return runtime_key


def _run_id(request_id: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{request_id}_provider_{stamp}"


def dispatch_layer_nine_option_acquisition(
    *,
    start_month: str,
    end_month: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    request_ids: Sequence[str] = (),
    limit: int | None = None,
    execute_provider_calls: bool = False,
    continue_on_error: bool = False,
    database_url: str | None = None,
    dynamic_workers: bool = True,
    max_workers: int = 4,
) -> ProviderDispatchSummary:
    """Plan or dispatch reviewed Layer 9 source_05 option snapshot acquisition."""

    rows = _layer_nine_request_rows(start_month=start_month, end_month=end_month, request_ids=request_ids, database_url=database_url)
    if limit is not None:
        if limit <= 0:
            raise TaskSystemError("limit must be positive")
        rows = rows[:limit]
    worker_selection = select_provider_worker_count(
        request_count=len(rows),
        execute_provider_calls=execute_provider_calls,
        dynamic_workers=dynamic_workers,
        max_workers=max_workers,
    )

    def dispatch_one(row: Mapping[str, Any], *, worker_slot: int) -> ProviderDispatchItem:
        request_id = str(row["request_id"])
        source_path = storage_root / str(row["parameter_ref"]).removeprefix("storage://trading-manager/")
        if not source_path.exists():
            raise TaskSystemError(f"Layer 9 option task key does not exist: {source_path}")
        task_key = json.loads(source_path.read_text(encoding="utf-8"))
        runtime_task_key = storage_root / "runtime" / "provider_task_keys" / request_id / "task_key.json"
        command_path = source_path
        runtime_retained = False
        if execute_provider_calls:
            runtime_task_key.parent.mkdir(parents=True, exist_ok=True)
            runtime_task_key.write_text(json.dumps(_runtime_task_key(task_key), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            command_path = runtime_task_key
            runtime_retained = True
        command = ["python3", "-m", "data_source.source_05_option_expression", str(command_path), "--run-id", _run_id(request_id)]
        receipt_path = str(Path(str(task_key.get("output_root") or "")) / "completion_receipt.json")
        status = "validated_not_dispatched"
        return_code = None
        error_tail = None
        if execute_provider_calls:
            result = subprocess.run(
                command,
                cwd=trading_data_root,
                env={**os.environ, "PYTHONPATH": str(trading_data_root / "src")},
                check=False,
                text=True,
                capture_output=True,
            )
            return_code = result.returncode
            status = "dispatched_succeeded" if result.returncode == 0 else "dispatched_failed"
            error_tail = "\n".join(part for part in (result.stdout[-500:], result.stderr[-500:]) if part) if result.returncode != 0 else None
            if result.returncode == 0:
                try:
                    runtime_task_key.unlink()
                    runtime_retained = False
                except FileNotFoundError:
                    runtime_retained = False
            if result.returncode != 0 and not continue_on_error:
                raise TaskSystemError(f"Layer 9 option source dispatch failed for {request_id}: {error_tail}")
        return ProviderDispatchItem(
            request_id=request_id,
            task_key_path=str(source_path),
            runtime_task_key_path=str(runtime_task_key) if execute_provider_calls and runtime_retained else None,
            runtime_task_key_retained=runtime_retained,
            command=command,
            receipt_path=receipt_path,
            status=status,
            worker_id=f"provider-worker-{worker_slot}",
            worker_slot=worker_slot,
            return_code=return_code,
            error_summary=error_tail,
        )

    items: list[ProviderDispatchItem] = []
    if worker_selection.selected_worker_count > 1:
        by_id: dict[str, ProviderDispatchItem] = {}
        with ThreadPoolExecutor(max_workers=worker_selection.selected_worker_count) as executor:
            futures = {
                executor.submit(dispatch_one, row, worker_slot=(index % worker_selection.selected_worker_count) + 1): str(row["request_id"])
                for index, row in enumerate(rows)
            }
            for future in as_completed(futures):
                by_id[futures[future]] = future.result()
        items.extend(by_id[str(row["request_id"])] for row in rows)
    else:
        items.extend(dispatch_one(row, worker_slot=1) for row in rows)
    dispatch_count = sum(1 for item in items if item.status in {"dispatched_succeeded", "dispatched_failed"})
    return ProviderDispatchSummary(
        contract_type="manager_provider_dispatch_summary",
        stage_id=STAGE_ID,
        request_count=len(rows),
        validation_count=0,
        dispatch_count=dispatch_count,
        provider_calls=dispatch_count,
        dispatch_performed=execute_provider_calls,
        model_activation_performed=False,
        broker_execution_performed=False,
        items=tuple(items),
        worker_selection=worker_selection,
    )


def write_gate_review(review: LayerNineGateReview, *, output: TextIO) -> None:
    json.dump(review.summary_row(), output, indent=2, sort_keys=True, default=str)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review the Layer 9 option-expression acquisition gate without provider calls.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--database-url")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--source-output-root", type=Path, default=DEFAULT_SOURCE_OUTPUT_ROOT)
    parser.add_argument("--write", action="store_true", help="Write review and receipt artifacts under --output-root.")
    parser.add_argument("--persist-sql", action="store_true", help="Persist reviewed Layer 9 option manager_request rows.")
    args = parser.parse_args(argv)
    review, _requests, _task_key_paths = prepare_layer_nine_option_acquisition(
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        output_root=args.output_root,
        source_output_root=args.source_output_root,
        write=args.write,
        persist_sql=args.persist_sql,
        database_url=args.database_url,
    )
    write_gate_review(review, output=sys.stdout)
    return 0 if review.status in {"no_provider_skip_accepted", "provider_acquisition_ready"} else 2


__all__ = [
    "LayerNineGateReview",
    "LayerNineRequestPreview",
    "build_layer_nine_gate_review",
    "fetch_layer_8_rows",
    "dispatch_layer_nine_option_acquisition",
    "manager_requests_from_gate_review",
    "prepare_layer_nine_option_acquisition",
    "request_previews_from_layer_8_rows",
    "write_layer_nine_task_keys",
    "write_gate_review_artifacts",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
