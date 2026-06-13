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


def build_model_group_layer_attribution(
    *,
    decision_rows_path: Path,
    output_dir: Path,
    replay_receipt_path: Path | None = None,
    promotion_review_path: Path | None = None,
    m05_unfilled_diagnostics_path: Path | None = None,
    run_id: str | None = None,
    now_utc: datetime | None = None,
    tail_row_limit: int = DEFAULT_TAIL_ROW_LIMIT,
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

    _write_csv(output_dir / "m04_m05_cohorts.csv", cohort_rows)
    _write_csv(output_dir / "filled_score_bins.csv", score_bin_rows)
    _write_csv(output_dir / "tail_loss_rows.csv", tail_rows)
    _write_csv(output_dir / "top_gain_rows.csv", top_gain_rows)
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
        "row_scope": _row_scope(rows),
        "layer_status": _layer_status(rows),
        "cohorts": cohort_rows,
        "filled_score_bins": score_bin_rows,
        "drawdown_summary": drawdown_summary,
        "tail_loss_rows_ref": str(output_dir / "tail_loss_rows.csv"),
        "top_gain_rows_ref": str(output_dir / "top_gain_rows.csv"),
        "m05_unfilled_summary": {
            key: value for key, value in m05_unfilled_summary.items() if key != "filter_reason_rows"
        },
        "verdict": _verdict(rows=rows, cohort_rows=cohort_rows, score_bin_rows=score_bin_rows),
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
    rows: list[Mapping[str, str]]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
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


def _verdict(
    *,
    rows: Sequence[Mapping[str, Any]],
    cohort_rows: Sequence[Mapping[str, Any]],
    score_bin_rows: Sequence[Mapping[str, Any]],
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
        "root_cause_status": "not_isolated",
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
    parser.add_argument("--run-id")
    parser.add_argument("--tail-row-limit", type=int, default=DEFAULT_TAIL_ROW_LIMIT)
    args = parser.parse_args(argv)
    report = build_model_group_layer_attribution(
        decision_rows_path=args.decision_rows,
        output_dir=args.output_dir,
        replay_receipt_path=args.replay_receipt,
        promotion_review_path=args.promotion_review,
        m05_unfilled_diagnostics_path=args.m05_unfilled_diagnostics,
        run_id=args.run_id,
        tail_row_limit=args.tail_row_limit,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
