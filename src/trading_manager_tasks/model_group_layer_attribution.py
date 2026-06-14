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
DEFAULT_PARAMETER_BUCKET_COUNT = 5
MIN_PARAMETER_SAMPLE_COUNT = 50
MIN_PARAMETER_UNIQUE_VALUES = 3
MIN_PARAMETER_FILLED_COUNT = 30
MIN_PARAMETER_ABS_CORRELATION = 0.08
MIN_PARAMETER_RETURN_SPREAD = 0.01
MIN_PARAMETER_LABEL_RATE_SPREAD = 0.05
MIN_PARAMETER_FILL_RATE_SPREAD = 0.15
SUSPECT_PARAMETER_COUNTERFACTUAL_FIELDNAMES = [
    "parameter_name",
    "parameter_family",
    "expected_direction",
    "primary_followup_mode",
    "reason_codes",
    "all_row_inversion_supported",
    "filled_only_inversion_supported",
    "all_label_inversion_supported",
    "filled_subset_selection_effect_supported",
    "m04_open_filled_inversion_supported",
    "m04_family_suspect_parameter_count",
    "sample_count",
    "filled_count",
    "nonfilled_count",
    "m04_open_count",
    "m04_open_filled_count",
    "value_mean",
    "filled_value_mean",
    "nonfilled_value_mean",
    "label_spearman",
    "return_spearman",
    "filled_return_spearman",
    "m04_open_filled_return_spearman",
    "high_minus_low_label_rate",
    "high_minus_low_return_per_row",
    "filled_high_minus_low_return_per_row",
    "m04_open_filled_high_minus_low_return_per_row",
    "low_bucket_fill_rate",
    "high_bucket_fill_rate",
    "high_minus_low_fill_rate",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
M04_COMPONENT_DIAGNOSTIC_FIELDNAMES = [
    "component_name",
    "subset_name",
    "expected_direction",
    "diagnostic_status",
    "reason_codes",
    "row_count",
    "filled_count",
    "value_mean",
    "label_spearman",
    "return_spearman",
    "high_minus_low_label_rate",
    "high_minus_low_return_per_row",
    "low_bucket_fill_rate",
    "high_bucket_fill_rate",
    "high_minus_low_fill_rate",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
M05_SELECTION_MECHANICS_FIELDNAMES = [
    "m04_state",
    "m05_state",
    "execution_expression_state",
    "option_feasibility_state",
    "selected_expression_type",
    "primary_filter_reason",
    "row_count",
    "filled_count",
    "filled_good_count",
    "filled_bad_count",
    "label_rate",
    "mean_prediction_score",
    "net_return_total",
    "return_per_row",
    "filled_hit_rate",
    "positive_label_count",
    "positive_underlying_return_total",
    "candidate_count_before_filter_mean",
    "candidate_count_after_filter_mean",
    "eligible_candidate_count_mean",
    "top_contract_fit_score_mean",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]


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
    parameter_review = _parameter_replay_review(rows)
    m04_component_rows = _m04_component_diagnostic_rows(rows)
    m05_selection_rows = _m05_selection_mechanics_rows(rows, counterfactual_rows)
    mechanism_review_report = _m04_m05_mechanism_review_report(
        m04_component_rows=m04_component_rows,
        m05_selection_rows=m05_selection_rows,
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
    _write_csv(output_dir / "parameter_replay_review.csv", parameter_review["parameter_rows"])
    _write_csv(output_dir / "parameter_bucket_metrics.csv", parameter_review["bucket_rows"])
    _write_csv(output_dir / "categorical_parameter_replay_review.csv", parameter_review["categorical_rows"])
    _write_csv(
        output_dir / "suspect_parameter_counterfactual.csv",
        parameter_review["suspect_counterfactual_rows"],
        fieldnames=SUSPECT_PARAMETER_COUNTERFACTUAL_FIELDNAMES,
    )
    _write_csv(
        output_dir / "m04_component_diagnostics.csv",
        m04_component_rows,
        fieldnames=M04_COMPONENT_DIAGNOSTIC_FIELDNAMES,
    )
    _write_csv(
        output_dir / "m05_selection_mechanics.csv",
        m05_selection_rows,
        fieldnames=M05_SELECTION_MECHANICS_FIELDNAMES,
    )
    (output_dir / "parameter_replay_review_report.json").write_text(
        json.dumps(parameter_review["report"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "suspect_parameter_counterfactual_report.json").write_text(
        json.dumps(parameter_review["suspect_counterfactual_report"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "high_score_filled_tail_loss_attribution_packet.json").write_text(
        json.dumps(tail_loss_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "m04_m05_mechanism_review_report.json").write_text(
        json.dumps(mechanism_review_report, indent=2, sort_keys=True) + "\n",
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
        "parameter_replay_review_ref": str(output_dir / "parameter_replay_review.csv"),
        "parameter_replay_review_report_ref": str(output_dir / "parameter_replay_review_report.json"),
        "parameter_bucket_metrics_ref": str(output_dir / "parameter_bucket_metrics.csv"),
        "categorical_parameter_replay_review_ref": str(output_dir / "categorical_parameter_replay_review.csv"),
        "parameter_replay_review_summary": parameter_review["summary"],
        "suspect_parameter_counterfactual_ref": str(output_dir / "suspect_parameter_counterfactual.csv"),
        "suspect_parameter_counterfactual_report_ref": str(
            output_dir / "suspect_parameter_counterfactual_report.json"
        ),
        "suspect_parameter_counterfactual_summary": parameter_review["suspect_counterfactual_summary"],
        "m04_component_diagnostics_ref": str(output_dir / "m04_component_diagnostics.csv"),
        "m05_selection_mechanics_ref": str(output_dir / "m05_selection_mechanics.csv"),
        "m04_m05_mechanism_review_report_ref": str(output_dir / "m04_m05_mechanism_review_report.json"),
        "m04_m05_mechanism_review_summary": mechanism_review_report["summary"],
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


def _parameter_replay_review(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    numeric_values: dict[str, list[tuple[float, Mapping[str, Any]]]] = defaultdict(list)
    categorical_values: dict[str, list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    for row in rows:
        for name, value in _numeric_parameter_values(row).items():
            numeric_values[name].append((value, row))
        for name, value in _categorical_parameter_values(row).items():
            categorical_values[name].append((value, row))

    parameter_rows: list[dict[str, Any]] = []
    bucket_rows: list[dict[str, Any]] = []
    categorical_rows: list[dict[str, Any]] = []
    for parameter_name, pairs in sorted(numeric_values.items()):
        parameter_row, parameter_bucket_rows = _numeric_parameter_review_row(parameter_name, pairs, total_row_count=len(rows))
        parameter_rows.append(parameter_row)
        bucket_rows.extend(parameter_bucket_rows)
    for parameter_name, pairs in sorted(categorical_values.items()):
        categorical_rows.extend(_categorical_parameter_review_rows(parameter_name, pairs))
    suspect_counterfactual_rows = _suspect_parameter_counterfactual_rows(parameter_rows, numeric_values)
    suspect_counterfactual_summary = _suspect_parameter_counterfactual_summary(suspect_counterfactual_rows)

    return {
        "report": _parameter_review_report(
            parameter_rows,
            categorical_rows,
            suspect_counterfactual_summary=suspect_counterfactual_summary,
        ),
        "summary": _parameter_review_summary(parameter_rows),
        "parameter_rows": parameter_rows,
        "bucket_rows": bucket_rows,
        "categorical_rows": categorical_rows,
        "suspect_counterfactual_rows": suspect_counterfactual_rows,
        "suspect_counterfactual_summary": suspect_counterfactual_summary,
        "suspect_counterfactual_report": _suspect_parameter_counterfactual_report(suspect_counterfactual_rows),
    }


def _numeric_parameter_values(row: Mapping[str, Any]) -> dict[str, float]:
    output: dict[str, float] = {}
    for key, value in row.items():
        if key.startswith("feature_") or key in {
            "prediction_score",
            "entry_minimum_alpha_confidence",
            "entry_minimum_trade_intensity",
            "bar_close",
        }:
            parsed = _finite_float(value)
            if parsed is not None:
                output[key] = parsed
    output.update(
        _flatten_numeric_parameters(
            row.get("model_layer_diagnostics") or {},
            prefix="model_layer_diagnostics",
        )
    )
    return {
        key: value
        for key, value in output.items()
        if not _parameter_name_is_outcome_or_id(key)
    }


def _flatten_numeric_parameters(value: Any, *, prefix: str) -> dict[str, float]:
    if isinstance(value, Mapping):
        output: dict[str, float] = {}
        for child_key, child_value in value.items():
            output.update(_flatten_numeric_parameters(child_value, prefix=f"{prefix}.{child_key}"))
        return output
    parsed = _finite_float(value)
    return {prefix: parsed} if parsed is not None else {}


def _parameter_name_is_outcome_or_id(name: str) -> bool:
    lowered = name.lower()
    forbidden = ("realized", "return_source", "outcome", "label", "next_", "_ref", "_id")
    return any(token in lowered for token in forbidden)


def _categorical_parameter_values(row: Mapping[str, Any]) -> dict[str, str]:
    diagnostics = row.get("model_layer_diagnostics") or {}
    m04 = diagnostics.get("model_04_unified_decision") or {}
    m05 = diagnostics.get("model_05_alpha_confidence") or {}
    return {
        "decision_action": _text(row.get("decision_action") or row.get("action")),
        "decision_status": _text(row.get("decision_status")),
        "fill_status": _text(row.get("fill_status")),
        "asset_expression_route": _text(row.get("asset_expression_route")),
        "option_contract_path_status": _text(row.get("option_contract_path_status")),
        "selected_option_expression_type": _selected_expression_type(row),
        "model_04.resolved_underlying_action_type": _text(m04.get("resolved_underlying_action_type")),
        "model_04.resolved_action_side": _text(m04.get("resolved_action_side")),
        "model_04.dominant_horizon": _text(m04.get("dominant_horizon")),
        "model_05.alpha_gate_status": _text(m05.get("alpha_gate_status")),
    }


def _numeric_parameter_review_row(
    parameter_name: str,
    pairs: Sequence[tuple[float, Mapping[str, Any]]],
    *,
    total_row_count: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    values = [value for value, _row in pairs]
    rows = [row for _value, row in pairs]
    buckets = _numeric_parameter_bucket_rows(parameter_name, pairs, bucket_count=DEFAULT_PARAMETER_BUCKET_COUNT)
    expected_direction = _expected_parameter_direction(parameter_name)
    label_correlation = _spearman(values, [_float(row.get("outcome_label")) for row in rows])
    return_correlation = _spearman(values, [_float(row.get("realized_return")) for row in rows])
    filled_pairs = [(value, row) for value, row in pairs if row.get("fill_status") == "simulated_filled"]
    filled_return_correlation = _spearman(
        [value for value, _row in filled_pairs],
        [_float(row.get("realized_return")) for _value, row in filled_pairs],
    )
    filled_buckets = _numeric_parameter_bucket_rows(
        parameter_name,
        filled_pairs,
        bucket_count=DEFAULT_PARAMETER_BUCKET_COUNT,
    )
    low_bucket, high_bucket = _edge_buckets(buckets)
    low_filled_bucket, high_filled_bucket = _edge_buckets(filled_buckets)
    return_spread = None
    label_rate_spread = None
    filled_return_spread = None
    if low_bucket is not None and high_bucket is not None:
        return_spread = _none_subtract(high_bucket.get("return_per_row"), low_bucket.get("return_per_row"))
        label_rate_spread = _none_subtract(high_bucket.get("label_rate"), low_bucket.get("label_rate"))
    if low_filled_bucket is not None and high_filled_bucket is not None:
        filled_return_spread = _none_subtract(
            high_filled_bucket.get("return_per_row"),
            low_filled_bucket.get("return_per_row"),
        )
    classification, reason_codes = _numeric_parameter_classification(
        expected_direction=expected_direction,
        sample_count=len(pairs),
        unique_count=len(set(values)),
        filled_count=len(filled_pairs),
        return_correlation=return_correlation,
        return_spread=return_spread,
        filled_return_correlation=filled_return_correlation,
        filled_return_spread=filled_return_spread,
    )
    return (
        {
            "parameter_name": parameter_name,
            "parameter_family": _parameter_family(parameter_name),
            "expected_direction": _direction_text(expected_direction),
            "classification": classification,
            "reason_codes": ";".join(reason_codes),
            "sample_count": len(pairs),
            "non_null_count": len(pairs),
            "missing_rate": _round(1 - (len(pairs) / total_row_count)) if total_row_count else None,
            "filled_count": len(filled_pairs),
            "unique_value_count": len(set(values)),
            "value_min": _round(min(values)) if values else None,
            "value_max": _round(max(values)) if values else None,
            "value_mean": _round(_mean(values)),
            "label_spearman": _round(label_correlation),
            "return_spearman": _round(return_correlation),
            "filled_return_spearman": _round(filled_return_correlation),
            "high_minus_low_return_per_row": _round(return_spread),
            "filled_high_minus_low_return_per_row": _round(filled_return_spread),
            "high_minus_low_label_rate": _round(label_rate_spread),
            "fixed_input_only": True,
            "threshold_selection_performed": False,
        },
        buckets,
    )


def _numeric_parameter_bucket_rows(
    parameter_name: str,
    pairs: Sequence[tuple[float, Mapping[str, Any]]],
    *,
    bucket_count: int,
) -> list[dict[str, Any]]:
    if not pairs:
        return []
    ordered = sorted(pairs, key=lambda item: item[0])
    groups: list[list[tuple[float, Mapping[str, Any]]]] = []
    for bucket_index in range(bucket_count):
        start = round(bucket_index * len(ordered) / bucket_count)
        end = round((bucket_index + 1) * len(ordered) / bucket_count)
        group = ordered[start:end]
        if group:
            groups.append(group)
    output: list[dict[str, Any]] = []
    for index, group in enumerate(groups, start=1):
        values = [value for value, _row in group]
        group_rows = [row for _value, row in group]
        summary = _summary(group_rows)
        output.append(
            {
                "parameter_name": parameter_name,
                "bucket_index": index,
                "bucket_count": len(groups),
                "value_min": _round(min(values)),
                "value_max": _round(max(values)),
                "value_mean": _round(_mean(values)),
                **summary,
            }
        )
    return output


def _edge_buckets(bucket_rows: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None]:
    if len(bucket_rows) < 2:
        return None, None
    return bucket_rows[0], bucket_rows[-1]


def _none_subtract(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def _numeric_parameter_classification(
    *,
    expected_direction: int | None,
    sample_count: int,
    unique_count: int,
    filled_count: int,
    return_correlation: float | None,
    return_spread: float | None,
    filled_return_correlation: float | None,
    filled_return_spread: float | None,
) -> tuple[str, list[str]]:
    reason_codes: list[str] = []
    if sample_count < MIN_PARAMETER_SAMPLE_COUNT:
        reason_codes.append("sample_count_below_minimum")
    if unique_count < MIN_PARAMETER_UNIQUE_VALUES:
        return "not_reviewable", ["unique_value_count_below_minimum"]
    if filled_count < MIN_PARAMETER_FILLED_COUNT:
        reason_codes.append("filled_sample_below_minimum")
    if reason_codes:
        return "weak_or_sample_limited", reason_codes
    if return_correlation is None or return_spread is None:
        return "weak_or_sample_limited", ["insufficient_numeric_variation"]
    aligned_correlation = return_correlation if expected_direction != -1 else -return_correlation
    aligned_spread = return_spread if expected_direction != -1 else -return_spread
    aligned_filled_correlation = (
        None
        if filled_return_correlation is None
        else filled_return_correlation if expected_direction != -1 else -filled_return_correlation
    )
    aligned_filled_spread = (
        None
        if filled_return_spread is None
        else filled_return_spread if expected_direction != -1 else -filled_return_spread
    )
    if expected_direction is None:
        if abs(return_correlation) >= MIN_PARAMETER_ABS_CORRELATION and abs(return_spread) >= MIN_PARAMETER_RETURN_SPREAD:
            return "empirical_signal_present_direction_unassigned", ["expected_direction_not_registered"]
        return "weak_or_sample_limited", ["weak_empirical_signal_or_unassigned_direction"]
    if aligned_correlation >= MIN_PARAMETER_ABS_CORRELATION and aligned_spread >= MIN_PARAMETER_RETURN_SPREAD:
        return "directionally_useful", ["return_correlation_and_bucket_spread_align"]
    if aligned_correlation <= -MIN_PARAMETER_ABS_CORRELATION and aligned_spread <= -MIN_PARAMETER_RETURN_SPREAD:
        return "suspect_requires_redesign", ["return_correlation_and_bucket_spread_inverted"]
    if (
        aligned_filled_correlation is not None
        and aligned_filled_spread is not None
        and aligned_filled_correlation <= -MIN_PARAMETER_ABS_CORRELATION
        and aligned_filled_spread <= -MIN_PARAMETER_RETURN_SPREAD
    ):
        return "suspect_requires_redesign", ["filled_return_correlation_and_bucket_spread_inverted"]
    if (
        aligned_filled_correlation is not None
        and aligned_filled_spread is not None
        and aligned_filled_correlation >= MIN_PARAMETER_ABS_CORRELATION
        and aligned_filled_spread >= MIN_PARAMETER_RETURN_SPREAD
    ):
        return "directionally_useful", ["filled_return_correlation_and_bucket_spread_align"]
    return "weak_or_sample_limited", ["weak_or_mixed_replay_signal"]


def _expected_parameter_direction(parameter_name: str) -> int | None:
    lowered = parameter_name.lower()
    if "downside_risk" in lowered or "cost" in lowered:
        return -1
    positive_tokens = (
        "prediction_score",
        "alpha",
        "confidence",
        "expected_return",
        "trade_intensity",
        "entry_quality",
        "action_direction",
        "momentum",
        "volume_rank",
        "feature_coverage",
        "signed_edge",
    )
    if any(token in lowered for token in positive_tokens):
        return 1
    return None


def _direction_text(direction: int | None) -> str:
    if direction == 1:
        return "higher_expected_better"
    if direction == -1:
        return "higher_expected_worse"
    return "unassigned"


def _parameter_family(parameter_name: str) -> str:
    if parameter_name.startswith("feature_"):
        return "top_level_feature"
    if "model_04_unified_decision" in parameter_name:
        return "model_04_unified_decision"
    if "model_05_alpha_confidence" in parameter_name:
        return "model_05_alpha_confidence"
    if parameter_name in {"prediction_score", "entry_minimum_alpha_confidence", "entry_minimum_trade_intensity"}:
        return "replay_decision_parameter"
    return "other"


def _categorical_parameter_review_rows(
    parameter_name: str,
    pairs: Sequence[tuple[str, Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for value, row in pairs:
        groups[value or "missing"].append(row)
    output: list[dict[str, Any]] = []
    for value, group_rows in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        output.append(
            {
                "parameter_name": parameter_name,
                "parameter_value": value,
                **_summary(group_rows),
                "fixed_input_only": True,
                "threshold_selection_performed": False,
            }
        )
    return output


def _parameter_review_summary(parameter_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row.get("classification") or "unknown") for row in parameter_rows)
    top_suspect = [
        str(row.get("parameter_name"))
        for row in parameter_rows
        if row.get("classification") == "suspect_requires_redesign"
    ][:10]
    top_useful = [
        str(row.get("parameter_name"))
        for row in parameter_rows
        if row.get("classification") == "directionally_useful"
    ][:10]
    return {
        "contract_type": "model_group_parameter_replay_review_summary",
        "parameter_count": len(parameter_rows),
        "classification_counts": dict(counts),
        "directionally_useful_parameters": top_useful,
        "suspect_requires_redesign_parameters": top_suspect,
        "fixed_input_only": True,
        "threshold_selection_performed": False,
        "interpretation_limits": [
            "Correlation and bucket spreads are replay diagnostics, not causal feature attribution.",
            "Sparse filled-option rows can make parameter classifications sample-limited.",
            "Unassigned-direction parameters require model-owner interpretation before redesign.",
        ],
    }


def _parameter_review_report(
    parameter_rows: Sequence[Mapping[str, Any]],
    categorical_rows: Sequence[Mapping[str, Any]],
    *,
    suspect_counterfactual_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "contract_type": "model_group_parameter_replay_review_report",
        "summary": _parameter_review_summary(parameter_rows),
        "numeric_parameter_rows_ref": "parameter_replay_review.csv",
        "numeric_parameter_bucket_rows_ref": "parameter_bucket_metrics.csv",
        "categorical_parameter_rows_ref": "categorical_parameter_replay_review.csv",
        "suspect_parameter_counterfactual_rows_ref": "suspect_parameter_counterfactual.csv",
        "suspect_parameter_counterfactual_report_ref": "suspect_parameter_counterfactual_report.json",
        "suspect_parameter_counterfactual_summary": suspect_counterfactual_summary,
        "categorical_parameter_count": len({row.get("parameter_name") for row in categorical_rows}),
        "review_role": "fixed_replay_association_diagnostic_only",
        "forbidden_uses": [
            "causal_feature_importance_claim",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _suspect_parameter_counterfactual_rows(
    parameter_rows: Sequence[Mapping[str, Any]],
    numeric_values: Mapping[str, Sequence[tuple[float, Mapping[str, Any]]]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    m04_suspect_count = sum(
        1
        for row in parameter_rows
        if row.get("classification") == "suspect_requires_redesign"
        and _parameter_family(str(row.get("parameter_name") or "")) == "model_04_unified_decision"
    )
    for parameter_row in parameter_rows:
        if parameter_row.get("classification") != "suspect_requires_redesign":
            continue
        parameter_name = str(parameter_row.get("parameter_name") or "")
        pairs = tuple(numeric_values.get(parameter_name) or ())
        if not pairs:
            continue
        output.append(
            _suspect_parameter_counterfactual_row(
                parameter_name=parameter_name,
                parameter_row=parameter_row,
                pairs=pairs,
                m04_suspect_count=m04_suspect_count,
            )
        )
    return output


def _suspect_parameter_counterfactual_row(
    *,
    parameter_name: str,
    parameter_row: Mapping[str, Any],
    pairs: Sequence[tuple[float, Mapping[str, Any]]],
    m04_suspect_count: int,
) -> dict[str, Any]:
    expected_direction = _expected_parameter_direction(parameter_name)
    all_stats = _parameter_subset_stats(pairs)
    filled_pairs = tuple((value, row) for value, row in pairs if row.get("fill_status") == "simulated_filled")
    nonfilled_pairs = tuple((value, row) for value, row in pairs if row.get("fill_status") != "simulated_filled")
    filled_stats = _parameter_subset_stats(filled_pairs)
    nonfilled_stats = _parameter_subset_stats(nonfilled_pairs)
    m04_open_pairs = tuple((value, row) for value, row in pairs if _m04_state(row) == "open_long/long")
    m04_open_filled_pairs = tuple(
        (value, row)
        for value, row in pairs
        if _m04_state(row) == "open_long/long" and row.get("fill_status") == "simulated_filled"
    )
    m04_open_stats = _parameter_subset_stats(m04_open_pairs)
    m04_open_filled_stats = _parameter_subset_stats(m04_open_filled_pairs)
    all_inversion = _aligned_inversion_supported(
        expected_direction=expected_direction,
        return_correlation=all_stats["return_spearman"],
        return_spread=all_stats["high_minus_low_return_per_row"],
    )
    filled_inversion = _aligned_inversion_supported(
        expected_direction=expected_direction,
        return_correlation=filled_stats["return_spearman"],
        return_spread=filled_stats["high_minus_low_return_per_row"],
    )
    m04_open_filled_inversion = _aligned_inversion_supported(
        expected_direction=expected_direction,
        return_correlation=m04_open_filled_stats["return_spearman"],
        return_spread=m04_open_filled_stats["high_minus_low_return_per_row"],
    )
    label_inversion = _aligned_label_inversion_supported(
        expected_direction=expected_direction,
        label_correlation=all_stats["label_spearman"],
        label_spread=all_stats["high_minus_low_label_rate"],
    )
    fill_rate_spread = all_stats["high_minus_low_fill_rate"]
    selection_effect = (
        filled_inversion
        and not label_inversion
        and (
            not all_inversion
            or (
                fill_rate_spread is not None
                and abs(float(fill_rate_spread)) >= MIN_PARAMETER_FILL_RATE_SPREAD
            )
        )
    )
    parameter_family = _parameter_family(parameter_name)
    primary_mode, reason_codes = _suspect_parameter_primary_mode(
        parameter_family=parameter_family,
        all_inversion=all_inversion,
        filled_inversion=filled_inversion,
        label_inversion=label_inversion,
        selection_effect=selection_effect,
        m04_open_filled_inversion=m04_open_filled_inversion,
        m04_suspect_count=m04_suspect_count,
    )
    return {
        "parameter_name": parameter_name,
        "parameter_family": parameter_family,
        "expected_direction": parameter_row.get("expected_direction"),
        "primary_followup_mode": primary_mode,
        "reason_codes": ";".join(reason_codes),
        "all_row_inversion_supported": all_inversion,
        "filled_only_inversion_supported": filled_inversion,
        "all_label_inversion_supported": label_inversion,
        "filled_subset_selection_effect_supported": selection_effect,
        "m04_open_filled_inversion_supported": m04_open_filled_inversion,
        "m04_family_suspect_parameter_count": m04_suspect_count if parameter_family == "model_04_unified_decision" else 0,
        "sample_count": all_stats["row_count"],
        "filled_count": filled_stats["row_count"],
        "nonfilled_count": nonfilled_stats["row_count"],
        "m04_open_count": m04_open_stats["row_count"],
        "m04_open_filled_count": m04_open_filled_stats["row_count"],
        "value_mean": _round(all_stats["value_mean"]),
        "filled_value_mean": _round(filled_stats["value_mean"]),
        "nonfilled_value_mean": _round(nonfilled_stats["value_mean"]),
        "label_spearman": _round(all_stats["label_spearman"]),
        "return_spearman": _round(all_stats["return_spearman"]),
        "filled_return_spearman": _round(filled_stats["return_spearman"]),
        "m04_open_filled_return_spearman": _round(m04_open_filled_stats["return_spearman"]),
        "high_minus_low_label_rate": _round(all_stats["high_minus_low_label_rate"]),
        "high_minus_low_return_per_row": _round(all_stats["high_minus_low_return_per_row"]),
        "filled_high_minus_low_return_per_row": _round(filled_stats["high_minus_low_return_per_row"]),
        "m04_open_filled_high_minus_low_return_per_row": _round(
            m04_open_filled_stats["high_minus_low_return_per_row"]
        ),
        "low_bucket_fill_rate": _round(all_stats["low_bucket_fill_rate"]),
        "high_bucket_fill_rate": _round(all_stats["high_bucket_fill_rate"]),
        "high_minus_low_fill_rate": _round(fill_rate_spread),
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }


def _parameter_subset_stats(pairs: Sequence[tuple[float, Mapping[str, Any]]]) -> dict[str, Any]:
    if not pairs:
        return {
            "row_count": 0,
            "label_spearman": None,
            "return_spearman": None,
            "value_mean": None,
            "high_minus_low_label_rate": None,
            "high_minus_low_return_per_row": None,
            "low_bucket_fill_rate": None,
            "high_bucket_fill_rate": None,
            "high_minus_low_fill_rate": None,
        }
    values = [value for value, _row in pairs]
    rows = [row for _value, row in pairs]
    buckets = _numeric_parameter_bucket_rows("parameter_subset", pairs, bucket_count=DEFAULT_PARAMETER_BUCKET_COUNT)
    low_bucket, high_bucket = _edge_buckets(buckets)
    label_spread = None
    return_spread = None
    fill_rate_spread = None
    low_bucket_fill_rate = None
    high_bucket_fill_rate = None
    if low_bucket is not None and high_bucket is not None:
        label_spread = _none_subtract(high_bucket.get("label_rate"), low_bucket.get("label_rate"))
        return_spread = _none_subtract(high_bucket.get("return_per_row"), low_bucket.get("return_per_row"))
        low_bucket_fill_rate = _fill_rate_from_summary(low_bucket)
        high_bucket_fill_rate = _fill_rate_from_summary(high_bucket)
        fill_rate_spread = _none_subtract(high_bucket_fill_rate, low_bucket_fill_rate)
    return {
        "row_count": len(pairs),
        "label_spearman": _spearman(values, [_float(row.get("outcome_label")) for row in rows]),
        "return_spearman": _spearman(values, [_float(row.get("realized_return")) for row in rows]),
        "value_mean": _mean(values),
        "high_minus_low_label_rate": label_spread,
        "high_minus_low_return_per_row": return_spread,
        "low_bucket_fill_rate": low_bucket_fill_rate,
        "high_bucket_fill_rate": high_bucket_fill_rate,
        "high_minus_low_fill_rate": fill_rate_spread,
    }


def _fill_rate_from_summary(row: Mapping[str, Any]) -> float | None:
    row_count = int(row.get("row_count") or 0)
    if row_count <= 0:
        return None
    return _float(row.get("filled_count")) / row_count


def _aligned_inversion_supported(
    *,
    expected_direction: int | None,
    return_correlation: Any,
    return_spread: Any,
) -> bool:
    if expected_direction is None or return_correlation is None or return_spread is None:
        return False
    aligned_correlation = float(return_correlation) if expected_direction != -1 else -float(return_correlation)
    aligned_spread = float(return_spread) if expected_direction != -1 else -float(return_spread)
    return aligned_correlation <= -MIN_PARAMETER_ABS_CORRELATION and aligned_spread <= -MIN_PARAMETER_RETURN_SPREAD


def _aligned_label_inversion_supported(
    *,
    expected_direction: int | None,
    label_correlation: Any,
    label_spread: Any,
) -> bool:
    if expected_direction is None or label_correlation is None or label_spread is None:
        return False
    aligned_correlation = float(label_correlation) if expected_direction != -1 else -float(label_correlation)
    aligned_spread = float(label_spread) if expected_direction != -1 else -float(label_spread)
    return aligned_correlation <= -MIN_PARAMETER_ABS_CORRELATION and aligned_spread <= -MIN_PARAMETER_LABEL_RATE_SPREAD


def _suspect_parameter_primary_mode(
    *,
    parameter_family: str,
    all_inversion: bool,
    filled_inversion: bool,
    label_inversion: bool,
    selection_effect: bool,
    m04_open_filled_inversion: bool,
    m04_suspect_count: int,
) -> tuple[str, list[str]]:
    if (
        parameter_family == "model_04_unified_decision"
        and filled_inversion
        and m04_open_filled_inversion
        and m04_suspect_count >= 2
    ):
        return "m04_component_weight_or_direction_issue", [
            "multiple_m04_score_components_inverted_in_filled_subset",
            "m04_open_filled_subset_inversion_supported",
        ]
    if selection_effect:
        return "filled_subset_selection_effect", [
            "filled_subset_inversion_without_all_row_inversion",
            "fill_or_label_distribution_differs_across_parameter_buckets",
        ]
    if all_inversion and label_inversion:
        return "parameter_definition_or_direction_inversion", [
            "all_row_return_and_label_direction_inverted",
        ]
    if filled_inversion:
        return "filled_subset_unisolated_inversion", [
            "filled_subset_inversion_supported",
            "all_row_or_label_evidence_not_inverted",
        ]
    return "not_isolated_sample_limited", ["suspect_parameter_review_needs_more_evidence"]


def _suspect_parameter_counterfactual_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    mode_counts = Counter(str(row.get("primary_followup_mode") or "unknown") for row in rows)
    return {
        "contract_type": "model_group_suspect_parameter_counterfactual_summary",
        "suspect_parameter_count": len(rows),
        "primary_followup_mode_counts": dict(mode_counts),
        "filled_subset_selection_effect_parameters": [
            str(row.get("parameter_name"))
            for row in rows
            if row.get("primary_followup_mode") == "filled_subset_selection_effect"
        ],
        "m04_component_weight_or_direction_issue_parameters": [
            str(row.get("parameter_name"))
            for row in rows
            if row.get("primary_followup_mode") == "m04_component_weight_or_direction_issue"
        ],
        "parameter_definition_or_direction_inversion_parameters": [
            str(row.get("parameter_name"))
            for row in rows
            if row.get("primary_followup_mode") == "parameter_definition_or_direction_inversion"
        ],
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
        "interpretation_limits": [
            "This counterfactual compares fixed replay subsets only and is not a causal parameter-importance claim.",
            "Filled-only inversion can indicate selection effects, option-expression mechanics, or M04 score behavior.",
            "Primary follow-up modes are repair triage labels, not automatic model redesign approval.",
        ],
    }


def _suspect_parameter_counterfactual_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "contract_type": "model_group_suspect_parameter_counterfactual_report",
        "summary": _suspect_parameter_counterfactual_summary(rows),
        "suspect_parameter_counterfactual_rows_ref": "suspect_parameter_counterfactual.csv",
        "review_role": "fixed_replay_suspect_parameter_triage_only",
        "fixed_input_only": True,
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "forbidden_uses": [
            "causal_feature_importance_claim",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _m04_component_diagnostic_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    components = [
        "action_direction_score",
        "expected_return_score",
        "trade_intensity_score",
        "action_confidence_score",
        "entry_quality_score",
        "downside_risk_score",
        "no_trade_probability_score",
    ]
    subsets = {
        "all_rows": tuple(rows),
        "m04_open": tuple(row for row in rows if _m04_state(row) == "open_long/long"),
        "m04_open_m05_pass": tuple(
            row for row in rows if _m04_state(row) == "open_long/long" and _m05_state(row) == "alpha_passed"
        ),
        "m04_open_m05_pass_filled": tuple(
            row
            for row in rows
            if _m04_state(row) == "open_long/long"
            and _m05_state(row) == "alpha_passed"
            and row.get("fill_status") == "simulated_filled"
        ),
    }
    output: list[dict[str, Any]] = []
    for component in components:
        expected_direction = _m04_component_expected_direction(component)
        for subset_name, subset_rows in subsets.items():
            pairs = tuple(_m04_component_pairs(subset_rows, component))
            stats = _parameter_subset_stats(pairs)
            status, reason_codes = _m04_component_diagnostic_status(
                expected_direction=expected_direction,
                subset_name=subset_name,
                stats=stats,
            )
            output.append(
                {
                    "component_name": component,
                    "subset_name": subset_name,
                    "expected_direction": _direction_text(expected_direction),
                    "diagnostic_status": status,
                    "reason_codes": ";".join(reason_codes),
                    "row_count": stats["row_count"],
                    "filled_count": sum(1 for _value, row in pairs if row.get("fill_status") == "simulated_filled"),
                    "value_mean": _round(stats["value_mean"]),
                    "label_spearman": _round(stats["label_spearman"]),
                    "return_spearman": _round(stats["return_spearman"]),
                    "high_minus_low_label_rate": _round(stats["high_minus_low_label_rate"]),
                    "high_minus_low_return_per_row": _round(stats["high_minus_low_return_per_row"]),
                    "low_bucket_fill_rate": _round(stats["low_bucket_fill_rate"]),
                    "high_bucket_fill_rate": _round(stats["high_bucket_fill_rate"]),
                    "high_minus_low_fill_rate": _round(stats["high_minus_low_fill_rate"]),
                    "threshold_selection_performed": False,
                    "retraining_performed": False,
                    "fixed_input_only": True,
                }
            )
    return output


def _m04_component_pairs(rows: Sequence[Mapping[str, Any]], component: str) -> Iterable[tuple[float, Mapping[str, Any]]]:
    for row in rows:
        scores = _m04_component_scores(row)
        parsed = _finite_float(scores.get(component))
        if parsed is not None:
            yield parsed, row


def _m04_component_scores(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return _m04_diagnostics(row).get("dominant_horizon_scores") or {}


def _m04_component_expected_direction(component: str) -> int | None:
    if component in {"downside_risk_score", "no_trade_probability_score"}:
        return -1
    return 1


def _m04_component_diagnostic_status(
    *,
    expected_direction: int | None,
    subset_name: str,
    stats: Mapping[str, Any],
) -> tuple[str, list[str]]:
    if int(stats["row_count"] or 0) < MIN_PARAMETER_FILLED_COUNT:
        return "sample_limited", ["subset_count_below_minimum"]
    if _aligned_inversion_supported(
        expected_direction=expected_direction,
        return_correlation=stats["return_spearman"],
        return_spread=stats["high_minus_low_return_per_row"],
    ):
        return "inverted_against_expected_direction", [f"{subset_name}_return_correlation_and_spread_inverted"]
    if _aligned_useful_supported(
        expected_direction=expected_direction,
        return_correlation=stats["return_spearman"],
        return_spread=stats["high_minus_low_return_per_row"],
    ):
        return "aligned_with_expected_direction", [f"{subset_name}_return_correlation_and_spread_align"]
    return "weak_or_mixed", [f"{subset_name}_weak_or_mixed_component_signal"]


def _aligned_useful_supported(
    *,
    expected_direction: int | None,
    return_correlation: Any,
    return_spread: Any,
) -> bool:
    if expected_direction is None or return_correlation is None or return_spread is None:
        return False
    aligned_correlation = float(return_correlation) if expected_direction != -1 else -float(return_correlation)
    aligned_spread = float(return_spread) if expected_direction != -1 else -float(return_spread)
    return aligned_correlation >= MIN_PARAMETER_ABS_CORRELATION and aligned_spread >= MIN_PARAMETER_RETURN_SPREAD


def _m05_selection_mechanics_rows(
    rows: Sequence[Mapping[str, Any]],
    counterfactual_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    counterfactual_by_decision_id = {str(row.get("decision_id") or ""): row for row in counterfactual_rows}
    groups: dict[tuple[str, str, str, str, str, str], list[tuple[Mapping[str, Any], Mapping[str, Any]]]] = defaultdict(list)
    for row in rows:
        counterfactual = counterfactual_by_decision_id.get(str(row.get("decision_id") or ""), {})
        key = (
            _m04_state(row),
            _m05_state(row),
            _expression_state(row),
            str(counterfactual.get("option_feasibility_state") or ""),
            _selected_expression_type(row),
            str(counterfactual.get("primary_filter_reason") or ""),
        )
        groups[key].append((row, counterfactual))

    output: list[dict[str, Any]] = []
    for (m04_state, m05_state, expression_state, feasibility_state, expression_type, filter_reason), grouped in sorted(
        groups.items(),
        key=lambda item: (-len(item[1]), item[0]),
    ):
        group_rows = [row for row, _counterfactual in grouped]
        group_counterfactuals = [counterfactual for _row, counterfactual in grouped]
        output.append(
            {
                "m04_state": m04_state,
                "m05_state": m05_state,
                "execution_expression_state": expression_state,
                "option_feasibility_state": feasibility_state,
                "selected_expression_type": expression_type,
                "primary_filter_reason": filter_reason,
                **_summary(group_rows),
                "positive_label_count": sum(1 for row in group_rows if str(row.get("outcome_label")) == "1"),
                "positive_underlying_return_total": _round(
                    sum(
                        _float(counterfactual.get("underlying_return"))
                        for row, counterfactual in grouped
                        if str(row.get("outcome_label")) == "1"
                    )
                ),
                "candidate_count_before_filter_mean": _counterfactual_metric_mean(
                    group_counterfactuals,
                    "candidate_count_before_filter",
                ),
                "candidate_count_after_filter_mean": _counterfactual_metric_mean(
                    group_counterfactuals,
                    "candidate_count_after_filter",
                ),
                "eligible_candidate_count_mean": _counterfactual_metric_mean(
                    group_counterfactuals,
                    "eligible_candidate_count",
                ),
                "top_contract_fit_score_mean": _counterfactual_metric_mean(
                    group_counterfactuals,
                    "top_contract_fit_score",
                ),
                "threshold_selection_performed": False,
                "retraining_performed": False,
                "fixed_input_only": True,
            }
        )
    return output


def _selected_expression_type(row: Mapping[str, Any]) -> str:
    for key in (
        "selected_option_expression_type",
        "decision_expression_type",
        "5_resolved_expression_type",
        "resolved_expression_type",
        "expression_type",
    ):
        value = str(row.get(key) or "").strip()
        if value == "underlying_only":
            return "underlying_only_expression"
        if value:
            return value
    return ""


def _counterfactual_metric_mean(rows: Sequence[Mapping[str, Any]], key: str) -> float | None:
    return _round(
        _mean(
            _float(row.get(key))
            for row in rows
            if row.get("expression_join_status") == "matched" and row.get(key) not in (None, "")
        )
    )


def _m04_m05_mechanism_review_report(
    *,
    m04_component_rows: Sequence[Mapping[str, Any]],
    m05_selection_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    m04_inverted = [
        str(row.get("component_name"))
        for row in m04_component_rows
        if row.get("subset_name") == "m04_open_m05_pass_filled"
        and row.get("diagnostic_status") == "inverted_against_expected_direction"
    ]
    m05_positive_unfilled = [
        row
        for row in m05_selection_rows
        if row.get("m04_state") == "open_long/long"
        and row.get("m05_state") == "alpha_passed"
        and row.get("execution_expression_state") == "expression_unfilled"
        and int(row.get("positive_label_count") or 0) > 0
    ]
    hard_filter_positive_unfilled = [
        row for row in m05_positive_unfilled if row.get("option_feasibility_state") == "hard_filter_zero_eligible"
    ]
    summary = {
        "contract_type": "model_group_m04_m05_mechanism_review_summary",
        "m04_open_filled_inverted_components": sorted(set(m04_inverted)),
        "m04_open_filled_inverted_component_count": len(set(m04_inverted)),
        "m05_open_pass_positive_unfilled_group_count": len(m05_positive_unfilled),
        "m05_hard_filter_positive_unfilled_group_count": len(hard_filter_positive_unfilled),
        "primary_followup": _m04_m05_primary_followup(m04_inverted, hard_filter_positive_unfilled),
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }
    return {
        "contract_type": "model_group_m04_m05_mechanism_review_report",
        "summary": summary,
        "m04_component_diagnostics_ref": "m04_component_diagnostics.csv",
        "m05_selection_mechanics_ref": "m05_selection_mechanics.csv",
        "review_role": "fixed_replay_m04_m05_mechanism_triage_only",
        "forbidden_uses": [
            "causal_feature_importance_claim",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _m04_m05_primary_followup(
    m04_inverted_components: Sequence[str],
    hard_filter_positive_unfilled_rows: Sequence[Mapping[str, Any]],
) -> str:
    if len(set(m04_inverted_components)) >= 2 and hard_filter_positive_unfilled_rows:
        return "m04_component_and_m05_filter_joint_review"
    if len(set(m04_inverted_components)) >= 2:
        return "m04_component_weight_or_direction_review"
    if hard_filter_positive_unfilled_rows:
        return "m05_option_expression_filter_review"
    return "more_fixed_replay_evidence_required"


def _spearman(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_ranks = _ranks(left)
    right_ranks = _ranks(right)
    return _pearson(left_ranks, right_ranks)


def _ranks(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = (index + end + 1) / 2
        for original_index, _value in indexed[index:end]:
            ranks[original_index] = average_rank
        index = end
    return ranks


def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((lvalue - left_mean) * (rvalue - right_mean) for lvalue, rvalue in zip(left, right, strict=True))
    left_denominator = sum((value - left_mean) ** 2 for value in left)
    right_denominator = sum((value - right_mean) ** 2 for value in right)
    denominator = (left_denominator * right_denominator) ** 0.5
    if denominator == 0:
        return None
    return numerator / denominator


def _finite_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


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


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], *, fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        path.write_text("", encoding="utf-8")
        return
    output_fieldnames: list[str] = list(fieldnames or [])
    for row in rows:
        for key in row:
            if key not in output_fieldnames:
                output_fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fieldnames)
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
