from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.model_group_layer_attribution import build_model_group_layer_attribution


class ModelGroupLayerAttributionTests(unittest.TestCase):
    def test_builds_m04_m05_boundary_report_without_mutation_flags(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            rows = [
                _row("r1", "accepted", "simulated_filled", 1, 0.82, 0.4, "open_long", "long", "passed", "listed_option_contract"),
                _row("r2", "accepted", "simulated_filled", 0, 0.83, -0.6, "open_long", "long", "passed", "listed_option_contract"),
                _row("r3", "suitable", "simulated_rejected", 1, 0.81, 0.0, "open_long", "long", "passed", "option_expression_unfilled"),
                _row("r4", "rejected", "simulated_rejected", 1, 0.79, 0.0, "no_trade", "none", "passed", ""),
                _row(
                    "r5",
                    "rejected",
                    "simulated_rejected",
                    0,
                    0.42,
                    0.0,
                    "no_trade",
                    "none",
                    "below_entry_threshold",
                    "",
                ),
            ]
            rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            m05_path = tmp / "m05_unfilled.csv"
            with m05_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["outcome_label", "plan_reason_codes", "fail_reason_counts"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "outcome_label": "1",
                        "plan_reason_codes": "no_contract_passed_hard_filter;dte_outside_policy_range",
                        "fail_reason_counts": "{'dte_outside_policy_range': 3, 'delta_outside_policy_range': 2}",
                    }
                )

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                m05_unfilled_diagnostics_path=m05_path,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            self.assertEqual(report["contract_type"], "model_group_layer_attribution_report")
            self.assertEqual(report["verdict"]["fault_surface"], "M04/M05 boundary")
            self.assertEqual(report["layer_status"]["m04_open_m05_pass_count"], 3)
            self.assertEqual(report["layer_status"]["m04_open_m05_pass_filled_count"], 2)
            self.assertEqual(report["layer_status"]["m04_open_m05_pass_expression_unfilled_count"], 1)
            self.assertEqual(report["layer_status"]["m05_pass_but_m04_not_open_count"], 1)
            self.assertFalse(report["side_effects"]["broker_execution_performed"])
            self.assertFalse(report["side_effects"]["sql_mutation_performed"])
            self.assertEqual(report["m05_unfilled_summary"]["filter_reason_counts"]["dte_outside_policy_range"], 3)
            self.assertTrue((output_dir / "layer_attribution_report.json").exists())
            self.assertTrue((output_dir / "m04_m05_cohorts.csv").exists())
            self.assertTrue((output_dir / "filled_score_bins.csv").exists())
            self.assertTrue((output_dir / "tail_loss_rows.csv").exists())


def _row(
    decision_id: str,
    decision_status: str,
    fill_status: str,
    outcome_label: int,
    prediction_score: float,
    realized_return: float,
    m04_action: str,
    m04_side: str,
    m05_status: str,
    route: str,
) -> dict[str, object]:
    return {
        "decision_id": decision_id,
        "timestamp": f"2021-01-0{decision_id[-1]}T16:00:00-05:00",
        "decision_status": decision_status,
        "fill_status": fill_status,
        "outcome_label": outcome_label,
        "prediction_score": prediction_score,
        "realized_return": realized_return,
        "asset_expression_route": route,
        "selected_option_contract_ref": "AAPL_2021-01-08_C_130" if fill_status == "simulated_filled" else "",
        "option_entry_price": 1.0,
        "option_exit_price": 1.0 + realized_return,
        "model_layer_diagnostics": {
            "model_04_unified_decision": {
                "resolved_underlying_action_type": m04_action,
                "resolved_action_side": m04_side,
                "reason_codes": ["resolved_open_long"] if m04_action == "open_long" else ["resolved_no_trade"],
                "dominant_horizon_scores": {"trade_intensity_score": 0.02},
            },
            "model_05_alpha_confidence": {
                "alpha_gate_status": m05_status,
                "resolved_alpha_score": prediction_score,
            },
        },
    }


if __name__ == "__main__":
    unittest.main()
