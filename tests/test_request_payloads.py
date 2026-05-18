from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.monthly_backfill import load_market_regime_universe, plan_monthly_backfill_requests
from trading_manager_tasks.request_payloads import (
    ALPACA_BARS_MONTHLY_MAX_PAGES,
    PARAMETER_SCHEMA_REF,
    build_request_task_payload,
    materialize_request_payload,
    storage_uri_to_local_path,
)


def _spy_layer_one_request() -> dict[str, object]:
    return next(
        row
        for row in plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")
        if row["target_component_id"] == "01_feed_alpaca_bars" and row.get("symbol") == "SPY"
    )


class RequestPayloadMaterializationTests(unittest.TestCase):
    def test_storage_uri_resolves_under_storage_root(self):
        path = storage_uri_to_local_path(
            "storage://trading-manager/monthly_backfill/alpaca_bars/SPY/2016-01/task_key.json",
            storage_root=Path("/tmp/manager-storage"),
        )

        self.assertEqual(path, Path("/tmp/manager-storage/monthly_backfill/alpaca_bars/SPY/2016-01/task_key.json"))

    def test_monthly_backfill_payload_uses_component_task_key_shape(self):
        request = _spy_layer_one_request()

        payload = build_request_task_payload(request)

        self.assertEqual(payload["contract_type"], PARAMETER_SCHEMA_REF)
        self.assertEqual(payload["task_id"], request["request_id"])
        self.assertEqual(payload["feed"], "01_feed_alpaca_bars")
        self.assertEqual(payload["source_id"], "alpaca_bars")
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["window"], {"start_date": "2016-01-01", "end_date_exclusive": "2016-02-01"})
        self.assertEqual(payload["params"]["symbol"], "SPY")
        self.assertEqual(payload["params"]["timeframe"], request["timeframe"])
        self.assertEqual(payload["params"]["start"], "2016-01-01")
        self.assertEqual(payload["params"]["end"], "2016-02-01")
        self.assertEqual(payload["params"]["max_pages"], ALPACA_BARS_MONTHLY_MAX_PAGES)
        self.assertEqual(payload["output_root"], "storage/monthly_backfill/alpaca_bars/SPY/2016-01")
        self.assertFalse(payload["manager_controls"]["allow_live_provider_calls"])
        self.assertFalse(payload["manager_controls"]["autonomous_historical_provider_acquisition"])
        self.assertEqual(payload["manager_controls"]["allowed_providers"], ["alpaca"])
        self.assertEqual(payload["manager_controls"]["allowed_endpoint_families"], ["bars"])
        self.assertEqual(payload["manager_controls"]["max_symbols"], 1)
        self.assertEqual(payload["manager_controls"]["max_requests"], ALPACA_BARS_MONTHLY_MAX_PAGES)
        self.assertEqual(payload["manager_controls"]["max_time_window"], "31d")

    def test_materialization_writes_payload_and_request_input_binding(self):
        request = _spy_layer_one_request()
        with tempfile.TemporaryDirectory() as tmp:
            materialized = materialize_request_payload(request, storage_root=Path(tmp), write_file=True)
            payload = json.loads(materialized.local_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["request_id"], request["request_id"])
        self.assertEqual(materialized.parameter_ref, request["parameter_ref"])
        self.assertTrue(materialized.content_hash.startswith("sha256:"))
        self.assertGreater(materialized.byte_size, 0)
        self.assertEqual(materialized.input_binding["contract_type"], "input_binding")
        self.assertEqual(materialized.input_binding["input_role"], "parameter_payload")
        self.assertEqual(materialized.input_binding["input_ref"], request["parameter_ref"])
        self.assertEqual(materialized.input_binding["schema_ref"], PARAMETER_SCHEMA_REF)
        self.assertIn("2016-01-01/2016-02-01", materialized.input_binding["time_window"])

    def test_all_2016_01_default_sources_emit_required_component_params(self):
        requests = plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")
        by_component = {row["target_component_id"]: build_request_task_payload(row) for row in requests}
        layer_one_bar_payloads = [
            build_request_task_payload(row) for row in requests if row["target_component_id"] == "01_feed_alpaca_bars"
        ]

        self.assertEqual(len(layer_one_bar_payloads), len(load_market_regime_universe()))
        self.assertIn("SPY", {payload["params"]["symbol"] for payload in layer_one_bar_payloads})
        self.assertEqual(by_component["02_feed_alpaca_liquidity"]["params"]["symbol"], "SPY")
        self.assertIn("symbols", by_component["03_feed_alpaca_news"]["params"])
        self.assertIn("topic_categories", by_component["05_feed_gdelt_news"]["params"])
        self.assertEqual(by_component["08_feed_sec_company_financials"]["params"]["cik"], "0000320193")
        self.assertEqual(by_component["10_feed_thetadata_option_primary_tracking"]["params"]["underlying"], "AAPL")
        self.assertIn("current_standard", by_component["11_feed_thetadata_option_event_timeline"]["params"])


if __name__ == "__main__":
    unittest.main()
