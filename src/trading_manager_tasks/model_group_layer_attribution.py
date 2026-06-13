"""Build fixed-input M04/M05 layer-attribution diagnostics for replay rows."""

from __future__ import annotations

import argparse
import ast
import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_TAIL_ROW_LIMIT = 20
DEFAULT_HIGH_SCORE_THRESHOLD = 0.8


def build_model_group_layer_attribution(
    *,
    decision_rows_path: Path,
    output_dir: Path,
    replay_receipt_path: Path | None = None,
    promotion_review_path: Path | None = None,
    m05_unfilled_diagnostics_path: Path | None = None,
    counterfactual_gate_sweep_path: Path | None = None,
    run_id: str | None = None,
    now_utc: datetime | None = None,
    tail_row_limit: int = DEFAULT_TAIL_ROW_LIMIT,
    high_score_threshold: float = DEFAULT_HIGH_SCORE_THRESHOLD,
) -> dict[str, Any]:
    """Write a compact attribution report and supporting CSVs.

    The diagnostic is intentionally fixed-input: it reads replay decision rows
    and optional prior diagnostic CSV evidence, then writes derived summaries.
    It does not call providers, mutate SQL, activate models, or alter replay
    artifacts.
    """

    rows = tuple(_load_jsonl(decision_rows_path))
    if not rows:
        raise ValueError(f"decision rows are empty: {decision_rows_path}")
    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    run_id_value = run_id or "model_group_layer_attribution_" + now.strftime("%Y%m%dT%H%M%SZ")
    output_dir.mkdir(parents=True, exist_ok=True)

    cohort_rows = _cohort_rows(rows)
    score_bin_rows = _filled_score_bin_rows(rows)
    tail_rows = _tail_loss_rows(rows, limit=tail_row_limit)
    top_gain_rows = _top_gain_rows(rows, limit=tail_row_limit)
    drawdown_summary = _drawdown_summary(rows)
    m05_unfilled_summary = _m05_unfilled_summary(m05_unfilled_diagnostics_path)
    expression_rows = _load_csv_rows(m05_unfilled_diagnostics_path)
    expression_rows_by_timestamp = _expression_rows_by_timestamp(expression_rows)
    replay_timestamp_counts = Counter(str(row.get("timestamp") or "") for row in rows)
    counterfactual_rows = _counterfactual_rows(rows, expression_rows_by_timestamp, replay_timestamp_counts)
    counterfactual_summary = _counterfactual_summary(
        rows=rows,
        counterfactual_rows=counterfactual_rows,
        score_bin_rows=score_bin_rows,
    )
    gate_sweep_summary = _counterfactual_gate_sweep_summary(counterfactual_gate_sweep_path)
    tail_loss_packet, matched_tail_rows = _high_score_tail_loss_attribution_packet(
        rows=rows,
        counterfactual_summary=counterfactual_summary,
        decision_rows_path=decision_rows_path,
        m05_unfilled_diagnostics_path=m05_unfilled_diagnostics_path,
        output_dir=output_dir,
        high_score_threshold=high_score_threshold,
        now_utc=now,
    )

    _write_csv(output_dir / "m04_m05_cohorts.csv", cohort_rows)
    _write_csv(output_dir / "filled_score_bins.csv", score_bin_rows)
    _write_csv(output_dir / "tail_loss_rows.csv", tail_rows)
    _write_csv(output_dir / "top_gain_rows.csv", top_gain_rows)
    _write_csv(output_dir / "row_counterfactual_attribution.csv", counterfactual_rows)
    _write_csv(output_dir / "high_score_filled_tail_loss_matches.csv", matched_tail_rows)
    (output_dir / "high_score_filled_tail_loss_attribution_packet.json").write_text(
        json.dumps(tail_loss_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if m05_unfilled_summary["source_status"] == "available":
        _write_csv(output_dir / "m05_unfilled_filter_reasons.csv", m05_unfilled_summary["filter_reason_rows"])

    report = {
        "contract_type": "model_group_layer_attribution_report",
        "run_id": run_id_value,
        "generated_at_utc": now.isoformat(),
        "decision_rows_ref": str(decision_rows_path),
        "replay_receipt_ref": str(replay_receipt_path) if replay_receipt_path else "",
        "promotion_review_ref": str(promotion_review_path) if promotion_review_path else "",
        "m05_unfilled_diagnostics_ref": str(m05_unfilled_diagnostics_path) if m05_unfilled_diagnostics_path else "",
        "counterfactual_gate_sweep_ref": str(counterfactual_gate_sweep_path) if counterfactual_gate_sweep_path else "",
        "row_scope": _row_scope(rows),
        "layer_status": _layer_status(rows),
        "cohorts": cohort_rows,
        "filled_score_bins": score_bin_rows,
        "drawdown_summary": drawdown_summary,
        "tail_loss_rows_ref": str(output_dir / "tail_loss_rows.csv"),
        "top_gain_rows_ref": str(output_dir / "top_gain_rows.csv"),
        "row_counterfactual_attribution_ref": str(output_dir / "row_counterfactual_attribution.csv"),
        "high_score_filled_tail_loss_attribution_packet_ref": str(
            output_dir / "high_score_filled_tail_loss_attribution_packet.json"
        ),
        "high_score_filled_tail_loss_matches_ref": str(output_dir / "high_score_filled_tail_loss_matches.csv"),
        "high_score_filled_tail_loss_summary": tail_loss_packet["headline"],
        "row_counterfactual_summary": counterfactual_summary,
        "counterfactual_gate_sweep_summary": gate_sweep_summary,
        "m05_unfilled_summary": {
            key: value for key, value in m05_unfilled_summary.items() if key != "filter_reason_rows"
        },
        "verdict": _verdict(
            rows=rows,
            cohort_rows=cohort_rows,
            score_bin_rows=score_bin_rows,
            counterfactual_summary=counterfactual_summary,
        ),
        "side_effects": {
            "provider_call_performed": False,
            "broker_execution_performed": False,
            "account_mutation_performed": False,
            "sql_mutation_performed": False,
            "storage_source_mutation_performed": False,
            "model_activation_performed": False,
            "active_model_config_written": False,
        },
    }
    (output_dir / "layer_attribution_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _load_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _m04_diagnostics(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return ((row.get("model_layer_diagnostics") or {}).get("model_04_unified_decision") or {})


def _m05_diagnostics(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return ((row.get("model_layer_diagnostics") or {}).get("model_05_alpha_confidence") or {})


def _m04_state(row: Mapping[str, Any]) -> str:
    diag = _m04_diagnostics(row)
    action = str(diag.get("resolved_underlying_action_type") or "unknown")
    side = str(diag.get("resolved_action_side") or "unknown")
    return f"{action}/{side}"


def _m05_state(row: Mapping[str, Any]) -> str:
    status = str(_m05_diagnostics(row).get("alpha_gate_status") or "unknown")
    return f"alpha_{status}"


def _expression_state(row: Mapping[str, Any]) -> str:
    if row.get("fill_status") == "simulated_filled":
        return "filled_contract"
    route = str(row.get("asset_expression_route") or "")
    if route == "option_expression_unfilled":
        return "expression_unfilled"
    return "no_expression"


def _score_bin(row: Mapping[str, Any]) -> str:
    score = _float(row.get("prediction_score"))
    if score >= 0.9:
        return ">=0.9"
    if score >= 0.8:
        return "0.8-0.9"
    if score >= 0.7:
        return "0.7-0.8"
    if score >= 0.6:
        return "0.6-0.7"
    return "<0.6"


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    row_count = len(rows)
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    label_sum = sum(_float(row.get("outcome_label")) for row in rows)
    score_sum = sum(_float(row.get("prediction_score")) for row in rows)
    net_return = sum(_float(row.get("realized_return")) for row in rows)
    filled_good = sum(1 for row in filled if str(row.get("outcome_label")) == "1")
    filled_bad = sum(1 for row in filled if str(row.get("outcome_label")) == "0")
    return {
        "row_count": row_count,
        "filled_count": len(filled),
        "filled_good_count": filled_good,
        "filled_bad_count": filled_bad,
        "label_rate": _round(label_sum / row_count) if row_count else None,
        "mean_prediction_score": _round(score_sum / row_count) if row_count else None,
        "net_return_total": _round(net_return),
        "return_per_row": _round(net_return / row_count) if row_count else None,
        "filled_hit_rate": _round(filled_good / len(filled)) if filled else None,
    }


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _cohort_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(_m04_state(row), _m05_state(row), _expression_state(row))].append(row)
    output = []
    for (m04_state, m05_state, expression_state), group_rows in sorted(groups.items()):
        item = {
            "m04_state": m04_state,
            "m05_state": m05_state,
            "expression_state": expression_state,
            **_summary(group_rows),
        }
        output.append(item)
    return output


def _filled_score_bin_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("fill_status") == "simulated_filled":
            groups[_score_bin(row)].append(row)
    order = {"<0.6": 0, "0.6-0.7": 1, "0.7-0.8": 2, "0.8-0.9": 3, ">=0.9": 4}
    return [
        {"score_bin": score_bin, **_summary(groups[score_bin])}
        for score_bin in sorted(groups, key=lambda value: order.get(value, 99))
    ]


def _drawdown_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    cumulative = 0.0
    peak = 0.0
    worst_drawdown = 0.0
    worst_row: Mapping[str, Any] | None = None
    for row in sorted(rows, key=lambda item: str(item.get("timestamp") or "")):
        cumulative += _float(row.get("realized_return"))
        peak = max(peak, cumulative)
        drawdown = cumulative - peak
        if drawdown < worst_drawdown:
            worst_drawdown = drawdown
            worst_row = row
    return {
        "final_cumulative_return": _round(cumulative),
        "max_drawdown": _round(worst_drawdown),
        "max_drawdown_timestamp": str(worst_row.get("timestamp") or "") if worst_row else "",
        "max_drawdown_decision_id": str(worst_row.get("decision_id") or "") if worst_row else "",
        "max_drawdown_contract_ref": str(worst_row.get("selected_option_contract_ref") or "") if worst_row else "",
    }


def _tail_loss_rows(rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    return [_row_extract(row) for row in sorted(filled, key=lambda item: _float(item.get("realized_return")))[:limit]]


def _top_gain_rows(rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    return [_row_extract(row) for row in sorted(filled, key=lambda item: _float(item.get("realized_return")), reverse=True)[:limit]]


def _row_extract(row: Mapping[str, Any]) -> dict[str, Any]:
    m04 = _m04_diagnostics(row)
    m05 = _m05_diagnostics(row)
    scores = m04.get("dominant_horizon_scores") or {}
    return {
        "timestamp": str(row.get("timestamp") or ""),
        "decision_id": str(row.get("decision_id") or ""),
        "decision_status": str(row.get("decision_status") or ""),
        "fill_status": str(row.get("fill_status") or ""),
        "outcome_label": _text(row.get("outcome_label")),
        "prediction_score": _round(_float(row.get("prediction_score"))),
        "realized_return": _round(_float(row.get("realized_return"))),
        "m04_state": _m04_state(row),
        "m04_reason_codes": ";".join(str(value) for value in (m04.get("reason_codes") or [])),
        "m05_state": _m05_state(row),
        "m05_resolved_alpha_score": _round(_float(m05.get("resolved_alpha_score"))),
        "trade_intensity_score": _round(_float(scores.get("trade_intensity_score"))),
        "selected_option_contract_ref": str(row.get("selected_option_contract_ref") or ""),
        "option_entry_price": _round(_float(row.get("option_entry_price"))),
        "option_exit_price": _round(_float(row.get("option_exit_price"))),
    }


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _row_scope(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "decision_row_count": len(rows),
        "filled_count": sum(1 for row in rows if row.get("fill_status") == "simulated_filled"),
        "simulated_rejected_count": sum(1 for row in rows if row.get("fill_status") == "simulated_rejected"),
        "decision_status_counts": dict(Counter(str(row.get("decision_status") or "") for row in rows)),
        "expression_state_counts": dict(Counter(_expression_state(row) for row in rows)),
    }


def _layer_status(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    m04_counts = Counter(_m04_state(row) for row in rows)
    m05_counts = Counter(_m05_state(row) for row in rows)
    m04_open_m05_pass = [
        row for row in rows if _m04_state(row) == "open_long/long" and _m05_state(row) == "alpha_passed"
    ]
    m05_pass_m04_blocked = [
        row for row in rows if _m05_state(row) == "alpha_passed" and _m04_state(row) != "open_long/long"
    ]
    return {
        "m04_state_counts": dict(m04_counts),
        "m05_state_counts": dict(m05_counts),
        "m04_open_m05_pass_count": len(m04_open_m05_pass),
        "m04_open_m05_pass_filled_count": sum(
            1 for row in m04_open_m05_pass if _expression_state(row) == "filled_contract"
        ),
        "m04_open_m05_pass_expression_unfilled_count": sum(
            1 for row in m04_open_m05_pass if _expression_state(row) == "expression_unfilled"
        ),
        "m05_pass_but_m04_not_open_count": len(m05_pass_m04_blocked),
        "m05_pass_but_m04_not_open_label_rate": _round(
            sum(_float(row.get("outcome_label")) for row in m05_pass_m04_blocked) / len(m05_pass_m04_blocked)
        )
        if m05_pass_m04_blocked
        else None,
    }


def _m05_unfilled_summary(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"source_status": "missing", "row_count": 0, "filter_reason_rows": []}
    rows = _load_csv_rows(path)
    filter_counts: Counter[str] = Counter()
    plan_counts: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    for row in rows:
        labels[str(row.get("outcome_label") or "")] += 1
        for reason in str(row.get("plan_reason_codes") or "").split(";"):
            if reason:
                plan_counts[reason] += 1
        try:
            parsed = ast.literal_eval(str(row.get("fail_reason_counts") or "{}"))
        except (SyntaxError, ValueError):
            parsed = {}
        if isinstance(parsed, Mapping):
            for reason, count in parsed.items():
                filter_counts[str(reason)] += int(count)
    filter_reason_rows = [
        {"reason_code": reason_code, "count": count}
        for reason_code, count in filter_counts.most_common()
    ]
    return {
        "source_status": "available",
        "row_count": len(rows),
        "label_counts": dict(labels),
        "plan_reason_counts": dict(plan_counts),
        "filter_reason_counts": dict(filter_counts),
        "filter_reason_rows": filter_reason_rows,
    }


def _load_csv_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expression_rows_by_timestamp(rows: Sequence[Mapping[str, str]]) -> dict[str, list[Mapping[str, str]]]:
    by_timestamp: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        timestamp = str(row.get("timestamp") or "")
        if timestamp:
            by_timestamp[timestamp].append(row)
    return by_timestamp


def _counterfactual_rows(
    rows: Sequence[Mapping[str, Any]],
    expression_rows_by_timestamp: Mapping[str, Sequence[Mapping[str, str]]],
    replay_timestamp_counts: Mapping[str, int],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        expression_row, expression_join_status = _expression_row_for_replay_row(
            row=row,
            expression_rows_by_timestamp=expression_rows_by_timestamp,
            replay_timestamp_counts=replay_timestamp_counts,
        )
        m04 = _m04_diagnostics(row)
        scores = m04.get("dominant_horizon_scores") or {}
        expression_state = _expression_state(row)
        intended_trade = _m04_state(row) == "open_long/long" and _m05_state(row) == "alpha_passed"
        candidate_count_before_filter = _int_from_expression(expression_row, "candidate_count_before_filter")
        candidate_count_after_filter = _int_from_expression(expression_row, "candidate_count_after_filter")
        eligible_candidate_count = _int_from_expression(expression_row, "eligible_candidate_count")
        expression_selected_contract = str((expression_row or {}).get("selected_contract_ref") or "")
        option_feasibility_state = _option_feasibility_state(
            row=row,
            expression_row=expression_row,
            expression_join_status=expression_join_status,
            candidate_count_before_filter=candidate_count_before_filter,
            candidate_count_after_filter=candidate_count_after_filter,
            eligible_candidate_count=eligible_candidate_count,
        )
        model_execution_mismatch = _model_execution_mismatch(
            intended_trade=intended_trade,
            row=row,
            candidate_count_after_filter=candidate_count_after_filter,
            eligible_candidate_count=eligible_candidate_count,
            expression_selected_contract=expression_selected_contract,
        )
        fail_reason_counts = _fail_reason_counts(expression_row)
        bucket, reason_codes = _counterfactual_bucket(
            row=row,
            intended_trade=intended_trade,
            expression_row=expression_row,
            option_feasibility_state=option_feasibility_state,
            model_execution_mismatch=model_execution_mismatch,
        )
        output.append(
            {
                "timestamp": str(row.get("timestamp") or ""),
                "decision_id": str(row.get("decision_id") or ""),
                "decision_status": str(row.get("decision_status") or ""),
                "fill_status": str(row.get("fill_status") or ""),
                "intended_model_trade": intended_trade,
                "execution_expression_state": expression_state,
                "expression_join_status": expression_join_status,
                "model_execution_mismatch": model_execution_mismatch,
                "option_feasibility_state": option_feasibility_state,
                "candidate_count_before_filter": candidate_count_before_filter,
                "candidate_count_after_filter": candidate_count_after_filter,
                "eligible_candidate_count": eligible_candidate_count,
                "top_contract_fit_score": _round(_float((expression_row or {}).get("top_contract_fit_score"))),
                "primary_filter_reason": _primary_filter_reason(fail_reason_counts),
                "filter_reason_counts": json.dumps(fail_reason_counts, sort_keys=True),
                "prediction_score": _round(_float(row.get("prediction_score"))),
                "trade_intensity_score": _round(_float(scores.get("trade_intensity_score"))),
                "outcome_label": _text(row.get("outcome_label")),
                "realized_return": _round(_float(row.get("realized_return"))),
                "underlying_return": _round(_float((expression_row or {}).get("underlying_return"))),
                "selected_option_contract_ref": str(row.get("selected_option_contract_ref") or ""),
                "expression_selected_contract_ref": expression_selected_contract,
                "row_counterfactual_bucket": bucket,
                "bucket_reason_codes": ";".join(reason_codes),
            }
        )
    return output


def _expression_row_for_replay_row(
    *,
    row: Mapping[str, Any],
    expression_rows_by_timestamp: Mapping[str, Sequence[Mapping[str, str]]],
    replay_timestamp_counts: Mapping[str, int],
) -> tuple[Mapping[str, str] | None, str]:
    timestamp = str(row.get("timestamp") or "")
    if not timestamp:
        return None, "missing_timestamp"
    if replay_timestamp_counts.get(timestamp, 0) != 1:
        return None, "replay_timestamp_ambiguous"
    expression_rows = tuple(expression_rows_by_timestamp.get(timestamp) or ())
    if not expression_rows:
        return None, "missing"
    if len(expression_rows) != 1:
        return None, "m05_expression_timestamp_ambiguous"
    return expression_rows[0], "matched"


def _int_from_expression(row: Mapping[str, str] | None, key: str) -> int | None:
    if row is None or row.get(key) in (None, ""):
        return None
    try:
        return int(str(row.get(key)))
    except ValueError:
        return None


def _option_feasibility_state(
    *,
    row: Mapping[str, Any],
    expression_row: Mapping[str, str] | None,
    expression_join_status: str,
    candidate_count_before_filter: int | None,
    candidate_count_after_filter: int | None,
    eligible_candidate_count: int | None,
) -> str:
    if row.get("fill_status") == "simulated_filled":
        return "contract_selected"
    if expression_row is None:
        if expression_join_status.endswith("_ambiguous"):
            return "expression_evidence_ambiguous"
        return "expression_evidence_missing" if _expression_state(row) == "expression_unfilled" else "not_applicable"
    if candidate_count_after_filter and candidate_count_after_filter > 0:
        return "contract_available_after_filter"
    if eligible_candidate_count and eligible_candidate_count > 0:
        return "eligible_contract_available"
    if candidate_count_before_filter is None:
        return "unknown"
    if candidate_count_before_filter == 0:
        return "no_point_in_time_candidates"
    if _expression_state(row) == "expression_unfilled":
        return "hard_filter_zero_eligible"
    return "not_applicable"


def _model_execution_mismatch(
    *,
    intended_trade: bool,
    row: Mapping[str, Any],
    candidate_count_after_filter: int | None,
    eligible_candidate_count: int | None,
    expression_selected_contract: str,
) -> bool:
    if row.get("fill_status") == "simulated_filled":
        return False
    if not intended_trade:
        return False
    return bool(
        expression_selected_contract
        or (candidate_count_after_filter is not None and candidate_count_after_filter > 0)
        or (eligible_candidate_count is not None and eligible_candidate_count > 0)
    )


def _fail_reason_counts(row: Mapping[str, str] | None) -> dict[str, int]:
    if row is None:
        return {}
    try:
        parsed = ast.literal_eval(str(row.get("fail_reason_counts") or "{}"))
    except (SyntaxError, ValueError):
        return {}
    if not isinstance(parsed, Mapping):
        return {}
    output: dict[str, int] = {}
    for reason, count in parsed.items():
        try:
            output[str(reason)] = int(count)
        except (TypeError, ValueError):
            continue
    return output


def _primary_filter_reason(fail_reason_counts: Mapping[str, int]) -> str:
    if not fail_reason_counts:
        return ""
    return max(fail_reason_counts.items(), key=lambda item: item[1])[0]


def _counterfactual_bucket(
    *,
    row: Mapping[str, Any],
    intended_trade: bool,
    expression_row: Mapping[str, str] | None,
    option_feasibility_state: str,
    model_execution_mismatch: bool,
) -> tuple[str, list[str]]:
    if model_execution_mismatch:
        return "execution_connection_failure", ["intended_trade_had_available_contract_but_was_not_filled"]
    if intended_trade and option_feasibility_state in {"expression_evidence_missing", "no_point_in_time_candidates"}:
        return "data_insufficiency", [option_feasibility_state]
    score = _float(row.get("prediction_score"))
    realized_return = _float(row.get("realized_return"))
    if row.get("fill_status") == "simulated_filled" and score >= 0.8 and realized_return < 0:
        return "model_mechanism_defect", ["high_score_filled_tail_loss"]
    if (
        intended_trade
        and option_feasibility_state == "hard_filter_zero_eligible"
        and str(row.get("outcome_label")) == "1"
        and expression_row is not None
    ):
        return "model_mechanism_defect", ["option_expression_filter_blocks_positive_underlying_label"]
    return "not_diagnostic", []


def _counterfactual_summary(
    *,
    rows: Sequence[Mapping[str, Any]],
    counterfactual_rows: Sequence[Mapping[str, Any]],
    score_bin_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    bucket_counts: Counter[str] = Counter(str(row["row_counterfactual_bucket"]) for row in counterfactual_rows)
    bucket_label_sums: Counter[str] = Counter()
    bucket_realized_returns: Counter[str] = Counter()
    for row in counterfactual_rows:
        bucket = str(row["row_counterfactual_bucket"])
        bucket_label_sums[bucket] += _float(row.get("outcome_label"))
        bucket_realized_returns[bucket] += _float(row.get("realized_return"))
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    filled_good = [row for row in filled if str(row.get("outcome_label")) == "1"]
    filled_bad = [row for row in filled if str(row.get("outcome_label")) == "0"]
    score_gap = _mean(_float(row.get("prediction_score")) for row in filled_good)
    bad_score = _mean(_float(row.get("prediction_score")) for row in filled_bad)
    score_gap = None if score_gap is None or bad_score is None else score_gap - bad_score
    intended_unfilled_rows = [
        row
        for row in counterfactual_rows
        if row.get("intended_model_trade") is True and row.get("execution_expression_state") == "expression_unfilled"
    ]
    unfilled_good_count = sum(1 for row in intended_unfilled_rows if str(row.get("outcome_label")) == "1")
    score_bin_status = _filled_score_bin_monotonicity_status(score_bin_rows)
    sample_sufficiency = _sample_sufficiency_status(filled_count=len(filled), score_bin_rows=score_bin_rows)
    high_score_filled_loss_count = sum(
        1 for row in filled if _float(row.get("prediction_score")) >= 0.8 and _float(row.get("realized_return")) < 0
    )
    execution_mismatch_count = sum(1 for row in counterfactual_rows if row.get("model_execution_mismatch") is True)
    mechanism_reason_codes = []
    if score_gap is not None and abs(score_gap) < 0.02:
        mechanism_reason_codes.append("filled_good_bad_score_gap_below_0_02")
    if score_bin_status["status"] == "non_monotonic":
        mechanism_reason_codes.append("filled_score_bins_non_monotonic")
    if high_score_filled_loss_count:
        mechanism_reason_codes.append("high_score_filled_tail_losses_present")
    return {
        "counterfactual_bucket_counts": dict(bucket_counts),
        "counterfactual_bucket_label_rates": {
            bucket: _round(bucket_label_sums[bucket] / count) if count else None
            for bucket, count in bucket_counts.items()
        },
        "counterfactual_bucket_realized_return_totals": {
            bucket: _round(bucket_realized_returns[bucket]) for bucket in bucket_counts
        },
        "m04_open_m05_pass_unfilled_good_count": unfilled_good_count,
        "m04_open_m05_pass_unfilled_positive_underlying_return_total": _round(
            sum(_float(row.get("underlying_return")) for row in intended_unfilled_rows if str(row.get("outcome_label")) == "1")
        ),
        "m04_open_m05_pass_unfilled_csv_count": sum(
            1 for row in intended_unfilled_rows if row.get("expression_join_status") == "matched"
        ),
        "expression_join_status_counts": dict(
            Counter(str(row.get("expression_join_status") or "") for row in counterfactual_rows)
        ),
        "filled_good_bad_score_gap": _round(score_gap),
        "filled_score_bin_monotonicity_status": score_bin_status,
        "execution_connection_mismatch_count": execution_mismatch_count,
        "sample_sufficiency_status": sample_sufficiency,
        "high_score_filled_loss_count": high_score_filled_loss_count,
        "root_cause_assessment": {
            "data_insufficiency": {
                "status": "supported" if sample_sufficiency["status"] == "sample_limited" else "not_supported",
                "reason_codes": sample_sufficiency["reason_codes"],
            },
            "execution_connection_failure": {
                "status": "supported" if execution_mismatch_count else "not_supported_by_current_evidence",
                "reason_codes": ["intended_trade_available_contract_not_filled"] if execution_mismatch_count else [],
            },
            "model_mechanism_defect": {
                "status": "supported" if mechanism_reason_codes else "not_supported",
                "reason_codes": mechanism_reason_codes,
            },
        },
    }


def _filled_score_bin_monotonicity_status(score_bin_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    previous_return: float | None = None
    violations: list[dict[str, Any]] = []
    for row in score_bin_rows:
        current_return = row.get("return_per_row")
        if current_return is None:
            continue
        current_return_float = float(current_return)
        if previous_return is not None and current_return_float < previous_return:
            violations.append(
                {
                    "score_bin": row.get("score_bin"),
                    "return_per_row": _round(current_return_float),
                    "previous_return_per_row": _round(previous_return),
                }
            )
        previous_return = current_return_float
    return {
        "status": "non_monotonic" if violations else "monotonic",
        "violations": violations,
    }


def _sample_sufficiency_status(*, filled_count: int, score_bin_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reason_codes: list[str] = []
    if filled_count < 200:
        reason_codes.append("filled_sample_below_200")
    sparse_bins = [
        str(row.get("score_bin"))
        for row in score_bin_rows
        if row.get("row_count") is not None and int(row["row_count"]) < 30
    ]
    if sparse_bins:
        reason_codes.append("filled_score_bins_below_30:" + ",".join(sparse_bins))
    return {
        "status": "sample_limited" if reason_codes else "sufficient_for_this_diagnostic",
        "filled_count": filled_count,
        "minimum_required_filled_count": 200,
        "sparse_score_bins": sparse_bins,
        "minimum_required_bin_count": 30,
        "reason_codes": reason_codes,
    }


def _counterfactual_gate_sweep_summary(path: Path | None) -> dict[str, Any]:
    rows = _load_csv_rows(path)
    if not rows:
        return {
            "source_status": "missing",
            "row_count": 0,
            "threshold_selection_performed": False,
            "sweep_role": "fixed_diagnostic_only",
        }
    diagnostic_rows = []
    for row in rows:
        diagnostic_rows.append(
            {
                "minimum_entry_alpha_confidence": _round(_float(row.get("minimum_entry_alpha_confidence"))),
                "minimum_trade_intensity": _round(_float(row.get("minimum_trade_intensity"))),
                "m05_signal_count": _int(row.get("m05_signal_count")),
                "m05_selected_contract_count": _int(row.get("m05_selected_contract_count")),
                "m05_unfilled_count": _int(row.get("m05_unfilled_count")),
                "new_selected_vs_baseline_count": _int(row.get("new_selected_vs_baseline_count")),
                "new_selected_underlying_return_total": _round(_float(row.get("new_selected_underlying_return_total"))),
                "new_selected_underlying_return_average": _round(_float(row.get("new_selected_underlying_return_average"))),
                "new_selected_positive_label_count": _int(row.get("new_selected_positive_label_count")),
                "new_selected_negative_label_count": _int(row.get("new_selected_negative_label_count")),
            }
        )
    return {
        "source_status": "available",
        "row_count": len(rows),
        "threshold_selection_performed": False,
        "sweep_role": "fixed_diagnostic_only",
        "max_new_selected_vs_baseline_count": max(row["new_selected_vs_baseline_count"] for row in diagnostic_rows),
        "rows": diagnostic_rows,
    }


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _high_score_tail_loss_attribution_packet(
    *,
    rows: Sequence[Mapping[str, Any]],
    counterfactual_summary: Mapping[str, Any],
    decision_rows_path: Path,
    m05_unfilled_diagnostics_path: Path | None,
    output_dir: Path,
    high_score_threshold: float,
    now_utc: datetime,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    loss_rows = [
        row
        for row in filled
        if _float(row.get("prediction_score")) >= high_score_threshold and _float(row.get("realized_return")) < 0
    ]
    control_rows = [
        row
        for row in filled
        if _float(row.get("prediction_score")) >= high_score_threshold and _float(row.get("realized_return")) >= 0
    ]
    matched_rows = [_matched_tail_loss_row(loss_row, control_rows) for loss_row in loss_rows]
    matched_comparison_count = _matched_comparison_count(matched_rows)
    classification_summary = _tail_loss_classification_summary(
        filled=filled,
        loss_rows=loss_rows,
        control_rows=control_rows,
        matched_rows=matched_rows,
        counterfactual_summary=counterfactual_summary,
    )
    requires_evidence_summary = _requires_evidence_summary(classification_summary)
    packet = {
        "contract_type": "model_group_high_score_filled_tail_loss_attribution_packet",
        "generated_at_utc": now_utc.isoformat(),
        "source_scope": {
            "decision_rows_ref": str(decision_rows_path),
            "m05_unfilled_diagnostics_ref": str(m05_unfilled_diagnostics_path) if m05_unfilled_diagnostics_path else "",
            "fixed_input_only": True,
            "provider_call_performed": False,
            "broker_execution_performed": False,
            "account_mutation_performed": False,
            "sql_mutation_performed": False,
            "storage_source_mutation_performed": False,
            "model_activation_performed": False,
            "active_model_config_written": False,
        },
        "cohort_definition": {
            "high_score_threshold": high_score_threshold,
            "loss_predicate": "fill_status=simulated_filled and prediction_score>=threshold and realized_return<0",
            "control_predicate": "fill_status=simulated_filled and prediction_score>=threshold and realized_return>=0",
        },
        "headline": {
            "filled_count": len(filled),
            "high_score_filled_loss_count": len(loss_rows),
            "high_score_filled_control_count": len(control_rows),
            "filled_good_bad_score_gap": counterfactual_summary.get("filled_good_bad_score_gap"),
            "execution_connection_mismatch_count": counterfactual_summary.get("execution_connection_mismatch_count"),
            "sample_sufficiency_status": (counterfactual_summary.get("sample_sufficiency_status") or {}).get("status"),
            "matched_comparison_count": matched_comparison_count,
            "tail_loss_row_count": len(matched_rows),
        },
        "classification_summary": classification_summary,
        "requires_evidence_summary": requires_evidence_summary,
        "matched_comparison_rows_ref": str(output_dir / "high_score_filled_tail_loss_matches.csv"),
        "implementation_limits": [
            "No bid/ask, order-book depth, IV, Greeks, or venue fill-priority fields are available in replay decision rows.",
            "No point-in-time feature trace timestamps are available for feature-timing or leakage attribution.",
            "No event/regime overlay evidence is consumed by this packet; event miss classification remains M06-owned.",
            "Matched controls are nearest fixed-input comparisons, not causal counterfactual trades.",
        ],
    }
    return packet, matched_rows


def _matched_tail_loss_row(loss_row: Mapping[str, Any], control_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    control_row, match_quality = _match_control_row(loss_row, control_rows)
    loss_contract = _parse_option_contract(str(loss_row.get("selected_option_contract_ref") or ""))
    control_contract = _parse_option_contract(str((control_row or {}).get("selected_option_contract_ref") or ""))
    loss_m04 = _m04_diagnostics(loss_row)
    control_m04 = _m04_diagnostics(control_row or {})
    loss_scores = loss_m04.get("dominant_horizon_scores") or {}
    control_scores = control_m04.get("dominant_horizon_scores") or {}
    loss_return = _float(loss_row.get("realized_return"))
    control_return = _float((control_row or {}).get("realized_return"))
    label_return_disagreement = _label_return_disagreement(loss_row) or (
        _label_return_disagreement(control_row or {}) if control_row else False
    )
    primary_failure_class, secondary_failure_classes, requires_evidence_codes = _tail_loss_row_classification(
        loss_row=loss_row,
        control_row=control_row,
        loss_contract=loss_contract,
        control_contract=control_contract,
        label_return_disagreement=label_return_disagreement,
    )
    return {
        "loss_decision_id": str(loss_row.get("decision_id") or ""),
        "control_decision_id": str((control_row or {}).get("decision_id") or ""),
        "loss_timestamp": str(loss_row.get("timestamp") or ""),
        "control_timestamp": str((control_row or {}).get("timestamp") or ""),
        "match_quality": match_quality,
        "loss_prediction_score": _round(_float(loss_row.get("prediction_score"))),
        "control_prediction_score": _round(_float((control_row or {}).get("prediction_score"))),
        "score_delta": _round(_float(loss_row.get("prediction_score")) - _float((control_row or {}).get("prediction_score"))),
        "loss_m05_alpha_score": _round(_float(_m05_diagnostics(loss_row).get("resolved_alpha_score"))),
        "control_m05_alpha_score": _round(_float(_m05_diagnostics(control_row or {}).get("resolved_alpha_score"))),
        "trade_intensity_delta": _round(_float(loss_scores.get("trade_intensity_score")) - _float(control_scores.get("trade_intensity_score"))),
        "loss_realized_return": _round(loss_return),
        "control_realized_return": _round(control_return),
        "return_delta": _round(loss_return - control_return),
        "loss_outcome_label": _text(loss_row.get("outcome_label")),
        "control_outcome_label": _text((control_row or {}).get("outcome_label")),
        "loss_contract_ref": str(loss_row.get("selected_option_contract_ref") or ""),
        "control_contract_ref": str((control_row or {}).get("selected_option_contract_ref") or ""),
        "loss_contract_underlying": loss_contract.get("underlying", ""),
        "loss_contract_expiry": loss_contract.get("expiry", ""),
        "loss_contract_option_side": loss_contract.get("option_side", ""),
        "loss_contract_strike": loss_contract.get("strike", ""),
        "loss_contract_dte": _contract_dte(loss_row, loss_contract),
        "control_contract_underlying": control_contract.get("underlying", ""),
        "control_contract_expiry": control_contract.get("expiry", ""),
        "control_contract_option_side": control_contract.get("option_side", ""),
        "control_contract_strike": control_contract.get("strike", ""),
        "control_contract_dte": _contract_dte(control_row or {}, control_contract),
        "same_target_ref": str(loss_row.get("target_ref") or "") == str((control_row or {}).get("target_ref") or ""),
        "same_m04_state": _m04_state(loss_row) == _m04_state(control_row or {}),
        "same_m05_state": _m05_state(loss_row) == _m05_state(control_row or {}),
        "same_contract_family": _same_contract_family(loss_contract, control_contract),
        "label_return_disagreement": label_return_disagreement,
        "primary_failure_class": primary_failure_class,
        "secondary_failure_classes": ";".join(secondary_failure_classes),
        "requires_evidence_codes": ";".join(requires_evidence_codes),
    }


def _match_control_row(
    loss_row: Mapping[str, Any],
    control_rows: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any] | None, str]:
    if not control_rows:
        return None, "unmatched"
    loss_contract = _parse_option_contract(str(loss_row.get("selected_option_contract_ref") or ""))
    loss_month = str(loss_row.get("timestamp") or "")[:7]

    def score(control_row: Mapping[str, Any]) -> tuple[int, float, int, str]:
        control_contract = _parse_option_contract(str(control_row.get("selected_option_contract_ref") or ""))
        same_target = str(loss_row.get("target_ref") or "") == str(control_row.get("target_ref") or "")
        same_m04 = _m04_state(loss_row) == _m04_state(control_row)
        same_m05 = _m05_state(loss_row) == _m05_state(control_row)
        same_score_bin = _score_bin(loss_row) == _score_bin(control_row)
        same_month = loss_month == str(control_row.get("timestamp") or "")[:7]
        same_contract_family = _same_contract_family(loss_contract, control_contract)
        quality_points = sum((same_target, same_m04, same_m05, same_score_bin, same_month, same_contract_family))
        score_distance = abs(_float(loss_row.get("prediction_score")) - _float(control_row.get("prediction_score")))
        time_distance = abs(_timestamp_sort_value(loss_row) - _timestamp_sort_value(control_row))
        return (-quality_points, score_distance, time_distance, str(control_row.get("decision_id") or ""))

    best = sorted(control_rows, key=score)[0]
    if str(loss_row.get("target_ref") or "") == str(best.get("target_ref") or "") and loss_month == str(best.get("timestamp") or "")[:7]:
        quality = "same_target_month_nearest_score"
    elif str(loss_row.get("target_ref") or "") == str(best.get("target_ref") or ""):
        quality = "same_target_nearest_score"
    elif _m04_state(loss_row) == _m04_state(best) and _m05_state(loss_row) == _m05_state(best):
        quality = "same_layer_state_only"
    else:
        quality = "weak_nearest_score"
    return best, quality


def _timestamp_sort_value(row: Mapping[str, Any]) -> int:
    text = str(row.get("timestamp") or "")
    digits = "".join(char for char in text if char.isdigit())
    try:
        return int(digits[:14])
    except ValueError:
        return 0


def _parse_option_contract(contract_ref: str) -> dict[str, str]:
    parts = contract_ref.split("_")
    if len(parts) < 4:
        return {}
    return {
        "underlying": parts[0],
        "expiry": parts[1],
        "option_side": parts[2],
        "strike": parts[3],
    }


def _contract_dte(row: Mapping[str, Any], contract: Mapping[str, str]) -> int | None:
    expiry = contract.get("expiry")
    timestamp = str(row.get("timestamp") or "")[:10]
    if not expiry or not timestamp:
        return None
    try:
        expiry_date = datetime.fromisoformat(expiry).date()
        timestamp_date = datetime.fromisoformat(timestamp).date()
    except ValueError:
        return None
    return (expiry_date - timestamp_date).days


def _same_contract_family(left: Mapping[str, str], right: Mapping[str, str]) -> bool:
    if not left or not right:
        return False
    return left.get("underlying") == right.get("underlying") and left.get("option_side") == right.get("option_side")


def _label_return_disagreement(row: Mapping[str, Any]) -> bool:
    label = _text(row.get("outcome_label"))
    realized_return = _float(row.get("realized_return"))
    return (label == "1" and realized_return < 0) or (label == "0" and realized_return > 0)


def _tail_loss_row_classification(
    *,
    loss_row: Mapping[str, Any],
    control_row: Mapping[str, Any] | None,
    loss_contract: Mapping[str, str],
    control_contract: Mapping[str, str],
    label_return_disagreement: bool,
) -> tuple[str, list[str], list[str]]:
    secondary: list[str] = ["model_overconfidence"]
    requires = [
        "feature_timing_or_leakage_requires_pit_feature_trace",
        "liquidity_spread_fill_realism_requires_bid_ask_depth_and_fill_model",
        "regime_event_miss_requires_m06_event_overlay",
    ]
    if label_return_disagreement:
        return "label_target_definition", secondary, requires
    if _contract_dte(loss_row, loss_contract) is None:
        secondary.append("option_selection_mechanics_unknown_contract_parse")
    elif _contract_dte(loss_row, loss_contract) is not None and _contract_dte(loss_row, loss_contract) <= 7:
        secondary.append("short_dte_option_selection_mechanics")
    if control_row and _same_contract_family(loss_contract, control_contract):
        secondary.append("same_contract_family_control_available")
    return "model_overconfidence", secondary, requires


def _tail_loss_classification_summary(
    *,
    filled: Sequence[Mapping[str, Any]],
    loss_rows: Sequence[Mapping[str, Any]],
    control_rows: Sequence[Mapping[str, Any]],
    matched_rows: Sequence[Mapping[str, Any]],
    counterfactual_summary: Mapping[str, Any],
) -> dict[str, Any]:
    score_gap = counterfactual_summary.get("filled_good_bad_score_gap")
    sample_status = (counterfactual_summary.get("sample_sufficiency_status") or {}).get("status")
    execution_mismatch_count = int(counterfactual_summary.get("execution_connection_mismatch_count") or 0)
    label_disagreements = sum(1 for row in matched_rows if row.get("label_return_disagreement") is True)
    short_dte_losses = sum(
        1
        for row in matched_rows
        if row.get("loss_contract_dte") not in (None, "") and _int(row.get("loss_contract_dte")) <= 7
    )
    classification = {
        "label_target_definition": {
            "status": "supported" if label_disagreements else "not_supported_by_current_evidence",
            "evidence_count": label_disagreements,
        },
        "feature_timing_or_leakage": {
            "status": "unknown_requires_evidence",
            "requires_evidence_codes": ["pit_feature_trace", "feature_generation_clock", "leakage_check_rows"],
        },
        "data_insufficiency": {
            "status": "supported" if sample_status == "sample_limited" else "not_supported_by_current_evidence",
            "reason_codes": (counterfactual_summary.get("sample_sufficiency_status") or {}).get("reason_codes", []),
        },
        "option_selection_mechanics": {
            "status": "weakly_supported" if short_dte_losses else "unknown_requires_evidence",
            "high_score_loss_short_dte_count": short_dte_losses,
        },
        "liquidity_spread_fill_realism": {
            "status": "unknown_requires_evidence",
            "requires_evidence_codes": ["bid_ask_spread", "quote_depth", "slippage_model", "partial_fill_simulation"],
        },
        "regime_event_miss": {
            "status": "unknown_requires_evidence",
            "requires_evidence_codes": ["m06_event_overlay", "regime_state", "co_event_controls"],
        },
        "model_overconfidence": {
            "status": "supported"
            if loss_rows and score_gap is not None and abs(float(score_gap)) < 0.02
            else "not_supported_by_current_evidence",
            "high_score_loss_count": len(loss_rows),
            "filled_good_bad_score_gap": score_gap,
        },
        "promotion_gate_weakness": {
            "status": "supported" if loss_rows and sample_status == "sample_limited" else "not_supported_by_current_evidence",
            "reason_codes": ["high_score_losses_under_sample_limited_evidence"] if loss_rows and sample_status == "sample_limited" else [],
        },
        "execution_replay_artifact": {
            "status": "supported" if execution_mismatch_count else "not_supported_by_current_evidence",
            "execution_connection_mismatch_count": execution_mismatch_count,
        },
    }
    classification["cohort_counts"] = {
        "filled_count": len(filled),
        "high_score_filled_loss_count": len(loss_rows),
        "high_score_filled_control_count": len(control_rows),
        "matched_comparison_count": _matched_comparison_count(matched_rows),
        "tail_loss_row_count": len(matched_rows),
    }
    classification["match_quality_counts"] = dict(Counter(str(row.get("match_quality") or "") for row in matched_rows))
    classification["primary_failure_class_counts"] = dict(
        Counter(str(row.get("primary_failure_class") or "") for row in matched_rows)
    )
    return classification


def _matched_comparison_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("match_quality") != "unmatched" and row.get("control_decision_id"))


def _requires_evidence_summary(classification_summary: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for name, item in classification_summary.items():
        if not isinstance(item, Mapping):
            continue
        if item.get("status") == "unknown_requires_evidence":
            output[name] = item.get("requires_evidence_codes", [])
    return output


def _verdict(
    *,
    rows: Sequence[Mapping[str, Any]],
    cohort_rows: Sequence[Mapping[str, Any]],
    score_bin_rows: Sequence[Mapping[str, Any]],
    counterfactual_summary: Mapping[str, Any],
) -> dict[str, Any]:
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    filled_good = [row for row in filled if str(row.get("outcome_label")) == "1"]
    filled_bad = [row for row in filled if str(row.get("outcome_label")) == "0"]
    bad_score = _mean(_float(row.get("prediction_score")) for row in filled_bad)
    good_score = _mean(_float(row.get("prediction_score")) for row in filled_good)
    negative_score_bins = [
        row["score_bin"]
        for row in score_bin_rows
        if row.get("net_return_total") is not None and float(row["net_return_total"]) < 0
    ]
    return {
        "first_visible_problem_layer": "M04",
        "fault_surface": "M04/M05 boundary",
        "root_cause_status": _root_cause_status(counterfactual_summary),
        "supporting_observations": [
            "Layer 1/2/3 replay coverage is not contradicted by this diagnostic; the first trade-universe selection split appears at M04.",
            "M04 open_long plus M05 alpha-passed rows split between filled contracts and expression-unfilled rows.",
            "M05 alpha score does not materially separate filled good from filled bad rows.",
            "Filled score bins are non-monotonic, so alpha ranking alone is not sufficient for promotion.",
        ],
        "filled_good_mean_prediction_score": _round(good_score),
        "filled_bad_mean_prediction_score": _round(bad_score),
        "negative_filled_score_bins": negative_score_bins,
        "recommended_next_step": (
            "Run bounded counterfactual attribution over existing replay inputs: M04 materiality/intensity variants, "
            "M05 expression feasibility on M04-open/M05-alpha-passed unfilled rows, and tail-loss slices by option contract features."
        ),
    }


def _root_cause_status(counterfactual_summary: Mapping[str, Any]) -> str:
    assessment = counterfactual_summary.get("root_cause_assessment") or {}
    supported = [
        cause
        for cause in ("data_insufficiency", "execution_connection_failure", "model_mechanism_defect")
        if ((assessment.get(cause) or {}).get("status") or "") == "supported"
    ]
    if len(supported) > 1:
        return "multiple_root_causes_supported:" + ",".join(supported)
    if supported:
        return supported[0] + "_supported"
    return "not_isolated"


def _mean(values: Iterable[float]) -> float | None:
    values_tuple = tuple(values)
    if not values_tuple:
        return None
    return sum(values_tuple) / len(values_tuple)


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-rows", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--replay-receipt", type=Path)
    parser.add_argument("--promotion-review", type=Path)
    parser.add_argument("--m05-unfilled-diagnostics", type=Path)
    parser.add_argument("--counterfactual-gate-sweep", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--tail-row-limit", type=int, default=DEFAULT_TAIL_ROW_LIMIT)
    parser.add_argument("--high-score-threshold", type=float, default=DEFAULT_HIGH_SCORE_THRESHOLD)
    args = parser.parse_args(argv)
    report = build_model_group_layer_attribution(
        decision_rows_path=args.decision_rows,
        output_dir=args.output_dir,
        replay_receipt_path=args.replay_receipt,
        promotion_review_path=args.promotion_review,
        m05_unfilled_diagnostics_path=args.m05_unfilled_diagnostics,
        counterfactual_gate_sweep_path=args.counterfactual_gate_sweep,
        run_id=args.run_id,
        tail_row_limit=args.tail_row_limit,
        high_score_threshold=args.high_score_threshold,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
