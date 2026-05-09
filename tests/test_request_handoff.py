from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from trading_manager_tasks.monthly_backfill import plan_monthly_backfill_requests
from trading_manager_tasks.request_handoff import validate_request_handoff
from trading_manager_tasks.request_payloads import materialize_request_payload


class RequestHandoffValidationTests(unittest.TestCase):
    def _fake_data_src(self, tmp: Path) -> Path:
        src = tmp / "trading-data-src"
        package = src / "data_feed" / "01_feed_alpaca_bars"
        package.mkdir(parents=True)
        (src / "data_feed" / "__init__.py").write_text("\n", encoding="utf-8")
        (package / "__init__.py").write_text("\n", encoding="utf-8")
        (package / "pipeline.py").write_text(
            textwrap.dedent(
                """
                from dataclasses import dataclass
                from pathlib import Path

                @dataclass(frozen=True)
                class Context:
                    run_dir: Path

                def build_context(task_key, run_id):
                    if task_key.get('feed') != '01_feed_alpaca_bars':
                        raise ValueError('wrong feed')
                    return Context(Path(task_key['output_root']) / 'runs' / run_id)
                """
            ),
            encoding="utf-8",
        )
        return src

    def test_validates_materialized_payload_with_component_build_context_only(self):
        request = plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")[0]
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            materialized = materialize_request_payload(request, storage_root=tmp, write_file=True)
            binding = dict(materialized.input_binding)

            result = validate_request_handoff(
                request,
                storage_root=tmp,
                component_src_root=self._fake_data_src(tmp),
                input_binding=binding,
                require_input_binding=True,
            )

        self.assertEqual(result.request_id, request["request_id"])
        self.assertEqual(result.target_component_id, "01_feed_alpaca_bars")
        self.assertTrue(result.content_hash.startswith("sha256:"))
        self.assertEqual(result.provider_calls, 0)
        self.assertFalse(result.dispatch_performed)
        self.assertEqual(result.context_run_dir, "storage/monthly_backfill_v1/alpaca_bars/2016-01/runs/manager_handoff_validation")

    def test_rejects_input_binding_hash_mismatch(self):
        request = plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")[0]
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            materialized = materialize_request_payload(request, storage_root=tmp, write_file=True)
            binding = dict(materialized.input_binding)
            binding["version_ref"] = "sha256:bad"

            with self.assertRaisesRegex(ValueError, "version_ref"):
                validate_request_handoff(
                    request,
                    storage_root=tmp,
                    component_src_root=self._fake_data_src(tmp),
                    input_binding=binding,
                    require_input_binding=True,
                )

    def test_rejects_payload_that_allows_live_calls(self):
        request = plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")[0]
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            materialized = materialize_request_payload(request, storage_root=tmp, write_file=True)
            payload = json.loads(materialized.local_path.read_text(encoding="utf-8"))
            payload["live_call_policy"]["allow_live_calls"] = True
            materialized.local_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "allow_live_calls"):
                validate_request_handoff(request, storage_root=tmp, component_src_root=self._fake_data_src(tmp))


if __name__ == "__main__":
    unittest.main()
