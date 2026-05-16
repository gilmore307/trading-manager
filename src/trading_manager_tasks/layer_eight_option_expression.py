"""Legacy physical option-expression gate review helpers.

This module is deliberately no-provider. It reviews completed conceptual Layer 6
underlying-action rows for option-expression-worthy actions before ThetaData
option-snapshot acquisition is prepared for the conceptual Layer 7 trading-guidance
boundary. If the month has no active underlying action chain, the correct legacy
``layer_08_option_expression`` acquisition outcome is a reviewed no-provider skip,
not an empty provider request.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError

DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_OUTPUT_ROOT = Path("storage/runtime/layer_08_option_expression/gate_review")
STAGE_ID = "layer_08_option_expression.data_acquisition"
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
class LayerEightRequestPreview:
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
    target_component_id: str = "source_05_option_expression"
    snapshot_type: str = "entry"

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LayerEightGateReview:
    """No-provider review of whether Layer 8 needs option-snapshot acquisition."""

    contract_type: str
    stage_id: str
    start_month: str
    end_month: str
    status: str
    reviewed_decision: str
    total_layer_7_rows: int
    active_target_chain_count: int
    active_request_count: int
    request_previews: tuple[LayerEightRequestPreview, ...]
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
    return f"mgrreq_layer8_option_snapshot_{underlying}_{start_month.replace('-', '_')}_{snapshot}_{target}"


def _is_active_layer_7_row(row: Mapping[str, Any]) -> bool:
    action_type = str(row.get("action_type") or "").strip().lower()
    action_side = str(row.get("action_side") or "").strip().lower()
    if action_type in INACTIVE_ACTION_TYPES:
        return False
    if action_side in INACTIVE_ACTION_SIDES and action_type not in ACTIVE_ACTION_TYPES:
        return False
    return True


def request_previews_from_layer_7_rows(rows: Iterable[Mapping[str, Any]], *, start_month: str) -> tuple[LayerEightRequestPreview, ...]:
    """Build future ThetaData request previews from active Layer 7 rows only."""

    previews: list[LayerEightRequestPreview] = []
    seen: set[str] = set()
    for row in rows:
        if not _is_active_layer_7_row(row):
            continue
        request_id = _request_id(row, start_month=start_month)
        if request_id in seen:
            continue
        seen.add(request_id)
        previews.append(
            LayerEightRequestPreview(
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


def build_layer_eight_gate_review(
    *,
    start_month: str,
    end_month: str,
    layer_7_rows: Sequence[Mapping[str, Any]],
    evidence_refs: Sequence[str] = (),
) -> LayerEightGateReview:
    previews = request_previews_from_layer_7_rows(layer_7_rows, start_month=start_month)
    if previews:
        status = "provider_acquisition_ready"
        reviewed_decision = "active_target_chain_ready_for_autonomous_option_acquisition"
        reason = f"{len(previews)} active Layer 7 target-chain rows are ready for autonomous ThetaData option snapshot acquisition before Layer 8 feature generation."
        recommended_next_action = "prepare_option_expression_acquisition"
    else:
        status = "no_provider_skip_accepted"
        reviewed_decision = "accepted_skip_no_active_target_chain"
        reason = "Layer 7 produced no active underlying-action chain for Layer 8; all rows are no-trade/maintain/neutral, so no option-chain provider call is warranted for this month."
        recommended_next_action = "record_layer_08_data_acquisition_no_provider_skip"
    return LayerEightGateReview(
        contract_type="manager_layer_08_option_expression_gate_review",
        stage_id=STAGE_ID,
        start_month=start_month,
        end_month=end_month,
        status=status,
        reviewed_decision=reviewed_decision,
        total_layer_7_rows=len(layer_7_rows),
        active_target_chain_count=len(previews),
        active_request_count=len(previews),
        request_previews=previews,
        evidence_refs=tuple(evidence_refs),
        reason=reason,
        recommended_next_action=recommended_next_action,
    )


def fetch_layer_7_rows(*, database_url: str, start_month: str, end_month: str) -> list[dict[str, Any]]:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    start = _month_start(start_month)
    end = _exclusive_month_start(end_month)
    query = """
        WITH target_symbols AS (
          SELECT DISTINCT ON (target_candidate_id)
                 target_candidate_id,
                 symbol AS underlying
          FROM trading_data.source_03_target_state
          ORDER BY target_candidate_id, available_time ASC
        )
        SELECT
          l7.available_time,
          l7.tradeable_time,
          l7.target_candidate_id,
          ts.underlying,
          COALESCE(l7.tradeable_time, l7.available_time) AS snapshot_time,
          l7.underlying_action_plan_ref,
          l7."7_resolved_underlying_action_type" AS action_type,
          l7."7_resolved_action_side" AS action_side,
          l7."7_resolved_dominant_horizon" AS dominant_horizon,
          l7."7_resolved_action_confidence_score" AS action_confidence_score
        FROM trading_model.model_07_underlying_action l7
        LEFT JOIN target_symbols ts USING (target_candidate_id)
        WHERE l7.available_time::timestamptz >= %s::timestamptz
          AND l7.available_time::timestamptz < %s::timestamptz
        ORDER BY l7.available_time::timestamptz ASC, l7.target_candidate_id ASC
    """
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (start, end))
            return [dict(row) for row in cursor.fetchall()]


def write_gate_review_artifacts(review: LayerEightGateReview, *, output_root: Path = DEFAULT_OUTPUT_ROOT) -> tuple[Path, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    review_path = output_root / f"layer_08_option_expression_gate_review_{review.start_month}.json"
    receipt_path = output_root / f"layer_08_option_expression_gate_review_receipt_{review.start_month}.json"
    review_payload = review.summary_row()
    review_payload["evidence_refs"] = [*review_payload["evidence_refs"], str(review_path), str(receipt_path)]
    review_path.write_text(json.dumps(review_payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    receipt_status = "succeeded" if review.status == "no_provider_skip_accepted" else "blocked"
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
                "run_id": f"layer_08_option_expression_gate_review_{review.start_month}",
                "status": receipt_status,
                "output_refs": [str(review_path)],
                "row_counts": {
                    "layer_7_rows_reviewed": review.total_layer_7_rows,
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


def write_gate_review(review: LayerEightGateReview, *, output: TextIO) -> None:
    json.dump(review.summary_row(), output, indent=2, sort_keys=True, default=str)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review the legacy layer_08 option-expression acquisition gate without provider calls.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--database-url")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--write", action="store_true", help="Write review and receipt artifacts under --output-root.")
    args = parser.parse_args(argv)
    rows = fetch_layer_7_rows(database_url=_database_url(args.database_url), start_month=args.start_month, end_month=args.end_month)
    review = build_layer_eight_gate_review(
        start_month=args.start_month,
        end_month=args.end_month,
        layer_7_rows=rows,
        evidence_refs=("sql:trading_model.model_07_underlying_action", "sql:trading_data.source_03_target_state"),
    )
    if args.write:
        review_path, receipt_path = write_gate_review_artifacts(review, output_root=args.output_root)
        review = LayerEightGateReview(**{**review.summary_row(), "request_previews": review.request_previews, "evidence_refs": (*review.evidence_refs, str(review_path), str(receipt_path))})
    write_gate_review(review, output=sys.stdout)
    return 0 if review.status == "no_provider_skip_accepted" else 2


__all__ = [
    "LayerEightGateReview",
    "LayerEightRequestPreview",
    "build_layer_eight_gate_review",
    "fetch_layer_7_rows",
    "request_previews_from_layer_7_rows",
    "write_gate_review_artifacts",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
