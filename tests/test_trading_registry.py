import csv
import json
import re
import unittest
from pathlib import Path

from trading_registry import (
    RegistryReader,
    SecretResolver,
    get_secret_entry_from_registry,
    map_registry_item_row,
    parse_registry,
)
from trading_manager_tasks.registry_values import registry_payload, registry_value


def create_row(**overrides):
    row = {
        "id": "fld_A7K3P2Q9",
        "kind": "field",
        "key": "REGISTRY_ITEM_ID",
        "payload_format": "text",
        "payload": "id",
        "path": None,
        "applies_to": "trading_registry",
        "artifact_sync_policy": "sync_artifact",
        "note": "canonical column name for trading_registry.id",
        "created_at": "2026-04-23T00:00:00.000Z",
        "updated_at": "2026-04-23T00:00:00.000Z",
    }
    row.update(overrides)
    return row


class RegistryHelperTests(unittest.TestCase):
    def test_registry_kind_files_match_sql_constraint_and_current_rows(self):
        schema = Path("scripts/registry/sql/trading_registry.sql").read_text()
        constraint = re.search(
            r"CONSTRAINT trading_registry_kind_check\s+CHECK \(kind IN \((.*?)\)\);",
            schema,
            re.S,
        ).group(1)
        constrained_kinds = sorted(re.findall(r"'([^']+)'", constraint))

        kind_files = sorted(
            path.stem
            for path in Path("scripts/registry/kinds").glob("*.md")
            if path.name != "README.md"
        )

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            current_kinds = {row["kind"] for row in csv.DictReader(csv_file)}

        self.assertEqual(kind_files, constrained_kinds)
        self.assertLessEqual(current_kinds, set(constrained_kinds))
        self.assertIn("payload_format", constrained_kinds)

    def test_registry_uses_current_table_sync_not_schema_migrations(self):
        self.assertTrue(Path("scripts/registry/sql/trading_registry.sql").is_file())
        self.assertTrue(Path("scripts/registry/sync_registry.py").is_file())
        self.assertFalse(Path("scripts/registry/sql/schema_migrations").exists())
        self.assertFalse(Path("scripts/registry/apply_registry_migrations.py").exists())

    def test_term_payloads_are_tokens_not_inline_prose_or_lists(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))

        generic_dictionary_keys = {
            "CODEX",
            "GITHUB",
            "OPENCLAW",
            "POSTGRESQL",
            "SMB",
            "SQL",
            "TAILSCALE",
            "TRADING_MANAGER_REGISTRY",
        }
        keys = {row["key"] for row in rows}
        self.assertFalse(generic_dictionary_keys & keys)

        bad_terms = [
            row["key"]
            for row in rows
            if row["kind"] == "term" and re.search(r"[\s;=]", row["payload"])
        ]
        self.assertEqual([], bad_terms)

    def test_term_rows_are_dictionary_entries_not_concrete_surfaces(self):
        artifact_suffixes = (
            "_CONTRACT",
            "_RECEIPT",
            "_MANIFEST",
            "_PACKET",
            "_RECORD",
            "_PLAN",
            "_SUMMARY",
            "_ARTIFACT",
            "_RESULT",
        )
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            term_rows = [
                row
                for row in csv.DictReader(csv_file)
                if row["kind"] == "term"
            ]

        offenders = []
        for row in term_rows:
            if row["key"].endswith("_TABLE"):
                offenders.append((row["key"], "sql_table"))
            if row["key"].endswith(artifact_suffixes):
                offenders.append((row["key"], "artifact_type"))
            if row["key"].startswith((
                "CANDIDATE_ANONYMITY_",
                "CANDIDATE_ELIGIBILITY_",
                "CANDIDATE_REASON_",
            )):
                offenders.append((row["key"], "status_value"))
            if row["key"].endswith("_POLICY") and row["payload"] not in {
                "model_06_dynamic_risk_policy",
                "layer_06_dynamic_risk_policy",
            }:
                offenders.append((row["key"], "config"))
            if (
                "/" in row["payload"]
                or row["payload"].endswith((".json", ".md"))
                or row["payload"].startswith("/root/")
            ):
                offenders.append((row["key"], "path_or_file_pattern"))
            if re.search(r"(20\d{6}|Q[1-4]_20\d{2})", row["key"]):
                offenders.append((row["key"], "dated_artifact"))
            if not row["note"].strip():
                offenders.append((row["key"], "missing_definition"))

        self.assertEqual([], offenders)

    def test_docs_decision_concepts_are_registered_as_terms(self):
        expected_payloads = {
            "accepted_event_failure_evidence",
            "activity_bridge_non_overlap",
            "blinded_agent_model_review",
            "contract_routed_component_work",
            "current_table_synced_registry",
            "evaluation_owned_replay_judgment",
            "execution_owned_runtime_lifecycle",
            "failure_attribution_boundary",
            "fold_completion_state",
            "full_run_cycle_promotion_gate",
            "gated_provider_call",
            "historical_modeling_boundary",
            "layer_3_candidate_selection_policy",
            "local_resumable_runtime_state",
            "manager_control_plane",
            "manager_scheduler_decision_loop",
            "model_worker_target_rotation",
            "optional_trading_guidance_expression",
            "post_replay_event_risk_governance",
            "reusable_foundation_catch_up",
            "script_called_agent_decision_surface",
            "startup_abnormality_scope",
            "target_substrate_lane",
            "six_model_stack",
        }
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            term_payloads = {
                row["payload"]
                for row in csv.DictReader(csv_file)
                if row["kind"] == "term"
            }

        self.assertLessEqual(expected_payloads, term_payloads)

    def test_sql_table_rows_use_sql_table_kind(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))

        sql_rows = [row for row in rows if row["kind"] == "sql_table"]
        self.assertTrue(sql_rows)
        self.assertFalse([
            row["key"]
            for row in rows
            if row["kind"] == "term" and row["key"].endswith("_TABLE")
        ])
        for row in sql_rows:
            self.assertIn("sql_table", row["applies_to"])
            self.assertTrue(row["key"].endswith("_TABLE"))
            self.assertTrue(
                "." in row["payload"]
                or row["payload"].startswith("model_")
            )

    def test_local_registry_paths_exist(self):
        repo_root = Path.cwd()
        missing = []

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            for row in csv.DictReader(csv_file):
                for raw_path in filter(None, (part.strip() for part in row["path"].split(";"))):
                    path_without_anchor = raw_path.split("#", 1)[0]
                    if not path_without_anchor:
                        continue

                    if path_without_anchor.startswith("/root/projects/trading-manager/"):
                        candidate = Path(path_without_anchor)
                    elif path_without_anchor.startswith("trading-manager/"):
                        candidate = repo_root / path_without_anchor.removeprefix("trading-manager/")
                    elif path_without_anchor.startswith(("scripts/", "src/", "tests/", "docs/", "deploy/", "schemas/")):
                        candidate = repo_root / path_without_anchor
                    else:
                        continue

                    if not candidate.exists():
                        missing.append(f"{row['key']} -> {raw_path}")

        self.assertEqual([], missing)

    def test_component_repository_rows_use_trading_data_and_manager_boundaries(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["TRADING_DATA_REPO"]["payload"], "trading-data")
        self.assertEqual(rows["TRADING_DATA_REPO"]["path"], "/root/projects/trading-data")
        self.assertIn("trading-data.git", rows["TRADING_DATA_REPO"]["note"])
        self.assertEqual(rows["TRADING_MANAGER_REPO"]["payload"], "trading-manager")
        self.assertEqual(rows["TRADING_MANAGER_REPO"]["path"], "/root/projects/trading-manager")
        self.assertIn("control-plane", rows["TRADING_MANAGER_REPO"]["note"])
        self.assertEqual(rows["TRADING_EVALUATION_REPO"]["payload"], "trading-evaluation")
        self.assertEqual(rows["TRADING_EVALUATION_REPO"]["path"], "/root/projects/trading-evaluation")
        self.assertIn("independent replay", rows["TRADING_EVALUATION_REPO"]["note"])
        self.assertNotIn("TRADING_MAIN_REPO", rows)
        self.assertNotIn("TRADING_SOURCE_REPO", rows)
        self.assertNotIn("TRADING_DERIVED_REPO", rows)
        self.assertNotIn("TRADING_STRATEGY_REPO", rows)
        for row in rows.values():
            self.assertNotIn("trading-" + "main", row["payload"])
            self.assertNotIn("trading-" + "main", row["path"])
            self.assertNotIn("trading-" + "source", row["payload"])
            self.assertNotIn("trading-" + "source", row["path"])
            self.assertNotIn("trading-" + "derived", row["payload"])
            self.assertNotIn("trading-" + "derived", row["path"])
            self.assertNotIn("trading-" + "strategy", row["payload"])
            self.assertNotIn("trading-" + "strategy", row["path"])

    def test_trading_evaluation_contract_rows_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        replay = rows["EVALUATION_REPLAY_CONTRACT"]
        self.assertEqual(replay["payload"], "evaluation_replay_contract")
        self.assertIn("same-target training-exclusion evidence", replay["note"])
        self.assertIn("target-context refs for non-ETF targets", replay["note"])
        self.assertIn("stress-exception refs for controlled data-edge cases", replay["note"])

        validation = rows["EVALUATION_REPLAY_CONTRACT_VALIDATION"]
        self.assertEqual(validation["payload"], "evaluation_replay_contract_validation")
        self.assertIn("replay target/window overlap", validation["note"])
        self.assertIn("non-ETF target-context refs", validation["note"])
        self.assertIn("stress-sleeve cap and exception refs", validation["note"])

        settlement = rows["FOLD_SETTLEMENT_RUN"]
        self.assertEqual(settlement["payload"], "fold_settlement_run")
        self.assertIn("completed fold", settlement["note"])

        eligibility = rows["PROMOTION_ELIGIBILITY_DECISION"]
        self.assertEqual(eligibility["payload"], "promotion_eligibility_decision")
        self.assertIn("eligible", eligibility["note"])
        self.assertIn("promotion-evaluation-review", eligibility["note"])

        readiness = rows["EVALUATION_PROMOTION_READINESS_RECORD"]
        self.assertEqual(readiness["payload"], "promotion_readiness_record")
        self.assertIn("trading-evaluation", readiness["path"])

        active_config = rows["EXECUTION_ACTIVE_MODEL_CONFIG"]
        self.assertEqual(active_config["payload"], "active_model_config")
        self.assertIn("trading-execution", active_config["path"])

        active_write = rows["EXECUTION_ACTIVE_MODEL_CONFIG_WRITE"]
        self.assertEqual(active_write["payload"], "execution_active_model_config_write")
        self.assertIn("rollback", active_write["note"])

        policy = rows["EVALUATION_PRIMARY_REPLAY_POLICY"]
        self.assertIn("candidate_policy_replay", policy["payload"])
        self.assertIn("canonical_2021_2025_historical_clock_replay", policy["payload"])
        self.assertIn("fixed_replay_window_2021_01_01_to_2026_01_01_end_exclusive", policy["payload"])
        self.assertIn("fixed_initial_capital_25000_usd", policy["payload"])
        self.assertIn("model_selects_targets_from_fixed_current_snapshot_candidate_universe", policy["payload"])
        self.assertIn("final_tickers_not_preselected", policy["payload"])
        self.assertIn("fixed_replay_window", policy["payload"])
        self.assertIn("fixed_selection_metrics", policy["payload"])
        self.assertIn("training_flow_replay_forbidden", policy["payload"])
        self.assertIn("overlapping_training_folds_blocked", policy["payload"])
        self.assertNotIn("EVALUATION_PRIMARY_REPLAY_CANDIDATE_SHARED_CSV", rows)
        self.assertNotIn("EVALUATION_PRIMARY_REPLAY_CANDIDATE_CSV_CONTRACT", rows)
        self.assertNotIn("REPLAY_CANDIDATE_STATUS", rows)
        self.assertNotIn("REPLAY_TIME_BUCKET_ID", rows)
        self.assertNotIn("REPLAY_SECTOR_COVERAGE_TAGS", rows)
        self.assertNotIn("REPLAY_EVENT_COVERAGE_TAGS", rows)
        self.assertNotIn("REPLAY_TRAINING_EXCLUSION_REASON", rows)
        initial_capital = rows["EVALUATION_REPLAY_INITIAL_CAPITAL_USD"]
        self.assertEqual(initial_capital["payload_format"], "decimal")
        self.assertEqual(initial_capital["payload"], "25000.0")
        self.assertIn("replay equity-path diagnostics", initial_capital["note"])
        self.assertIn("not broker account state", initial_capital["note"])
        self.assertIn(
            "prepare_replay_dataset.py",
            rows["TRADING_EVALUATION_PREPARE_REPLAY_DATASET"]["path"],
        )
        self.assertIn(
            "run_replay_acquisition.py",
            rows["TRADING_EVALUATION_RUN_REPLAY_ACQUISITION"]["path"],
        )
        self.assertIn("--execute", rows["TRADING_EVALUATION_RUN_REPLAY_ACQUISITION"]["note"])
        self.assertEqual(rows["REPLAY_DATASET_PREPARATION_MANIFEST"]["payload"], "replay_dataset_preparation_manifest")
        self.assertIn("manager_request_route_used=false", rows["REPLAY_DATASET_PREPARATION_MANIFEST"]["note"])
        self.assertIn("frozen reusable snapshot", rows["REPLAY_DATASET_PREPARATION_MANIFEST"]["note"])
        self.assertEqual(
            rows["REPLAY_REUSABLE_DATA_SNAPSHOT_POLICY"]["payload"],
            "one_time_acquisition_then_frozen_reuse",
        )
        self.assertIn("Candidate-specific replay data rebuilds are forbidden", rows["REPLAY_REUSABLE_DATA_SNAPSHOT_POLICY"]["note"])
        self.assertEqual(
            rows["REPLAY_REALTIME_REPLAY_ROUTE_POLICY"]["payload"],
            "historical_clock_realtime_execution_replay_not_training_flow",
        )
        self.assertIn("realtime execution decision path", rows["REPLAY_REALTIME_REPLAY_ROUTE_POLICY"]["note"])
        self.assertEqual(
            rows["PROMOTION_REPLAY_WINDOW_POLICY"]["payload"],
            "canonical_2021_01_01_to_2026_01_01_end_exclusive_1255_expected_trading_days",
        )
        self.assertNotIn("PROMOTION_REPLAY_TWO_YEAR_REPLAY_WINDOW", rows)
        self.assertEqual(
            rows["PROMOTION_REPLAY_CANDIDATE_POLICY_REPLAY_CONTRACT"]["payload"],
            "trading-evaluation/replays/promotion_replay_candidate_policy.json",
        )
        self.assertEqual(rows["REPLAY_FEED_ACQUISITION_PLAN"]["payload"], "replay_feed_acquisition_plan")
        self.assertIn("event-layer feeds", rows["REPLAY_FEED_ACQUISITION_PLAN"]["note"])
        self.assertEqual(rows["REPLAY_EVENT_LAYER_ACQUISITION_FEEDS"]["kind"], "config")
        self.assertEqual(
            rows["REPLAY_EVENT_LAYER_ACQUISITION_FEEDS"]["payload"],
            "03_feed_alpaca_news;05_feed_gdelt_news;08_feed_sec_company_financials",
        )
        self.assertEqual(rows["REPLAY_OPTION_CHAIN_SNAPSHOT_POLICY"]["payload"], "model_buy_point_triggered_chain_snapshots")
        self.assertIn("model buy/expression decisions", rows["REPLAY_OPTION_CHAIN_SNAPSHOT_POLICY"]["note"])
        duplicate_replay_phrase = " ".join(("replay", "replay"))
        self.assertNotIn(duplicate_replay_phrase, rows["REPLAY_OPTION_CHAIN_SNAPSHOT_POLICY"]["note"].lower())
        self.assertNotIn("REPLAY_FEED_TASK_PLAN", rows)
        self.assertEqual(rows["REPLAY_FEED_COVERAGE_STATUS_VALUES"]["payload"], "available;deferred;missing")
        self.assertIn("available/deferred/missing", rows["REPLAY_DATASET_PREPARATION_MANIFEST"]["note"])
        self.assertNotIn(duplicate_replay_phrase, rows["REPLAY_DATASET_PREPARATION_MANIFEST"]["note"].lower())
        self.assertNotIn(duplicate_replay_phrase, rows["REPLAY_REUSABLE_DATA_SNAPSHOT_POLICY"]["note"].lower())
        self.assertIn("deferred", rows["REPLAY_COVERAGE_SUMMARY"]["note"])
        self.assertEqual(
            rows["REPLAY_LIQUIDITY_FULL_HOURLY_ACQUISITION_POLICY"]["payload"],
            "full_hourly_regular_session_windows_per_component_month",
        )
        self.assertIn("Sampled liquidity receipts are smoke evidence only", rows["REPLAY_LIQUIDITY_FULL_HOURLY_ACQUISITION_POLICY"]["note"])
        self.assertNotIn("REPLAY_LIQUIDITY_SAMPLED_ACQUISITION_POLICY", rows)
        self.assertNotIn("REPLAY_FULL_MONTH_LIQUIDITY_DEFERRED_POLICY", rows)
        self.assertNotIn("REPLAY_LIQUIDITY_FULL_DAILY_ACQUISITION_POLICY", rows)
        self.assertEqual(rows["REPLAY_FEED_COVERAGE_STATUS_VALUES"]["kind"], "config")
        self.assertEqual(rows["OKX_HISTORICAL_REPLAY_CANDLE_ROUTE"]["payload"], "okx_history_candles_for_replay_windows")
        self.assertIn(
            "sealed one-time action",
            rows["REPLAY_ONE_SHOT_ACQUISITION_GATE_POLICY"]["note"],
        )
        self.assertNotIn("REPLAY_PROVIDER_TASK_KEYS_FAIL_CLOSED_POLICY", rows)

        review_skill = rows["EVALUATION_PROMOTION_REVIEW_SKILL"]
        self.assertEqual(review_skill["payload"], "promotion-evaluation-review")
        self.assertIn("promotion-evaluation-review/SKILL.md", review_skill["path"])
        self.assertIn("anonymous model comparison", review_skill["note"])

        vector_policy = rows["EVALUATION_PROMOTION_VECTOR_RUBRIC_POLICY"]
        self.assertIn("anonymous_model_vector_comparison", vector_policy["payload"])
        self.assertIn("defer_when_not_materially_better", vector_policy["payload"])

        readiness_policy = rows["EVALUATION_PROMOTION_READINESS_POLICY"]
        self.assertIn("evaluation_owns_offline_promotion_readiness", readiness_policy["payload"])
        self.assertIn("execution_owns_runtime_activation", readiness_policy["payload"])

        execution_policy = rows["EXECUTION_RUNTIME_MODEL_LIFECYCLE_POLICY"]
        self.assertIn("promoted_not_active_shadow_during_market_hours", execution_policy["payload"])
        self.assertIn("anonymous_model_comparison_required", execution_policy["payload"])
        self.assertIn("weekly_rerank", execution_policy["payload"])
        self.assertIn("one_active_three_stable_wingmen_two_rotating_challengers", execution_policy["payload"])
        self.assertIn("probation_uses_one_stable_wingman_slot", execution_policy["payload"])
        self.assertIn("probation_failed_expedited_elimination_review", execution_policy["payload"])
        self.assertIn("active_pointer_write_requires_separate_gate", execution_policy["payload"])
        self.assertIn("runtime promoted eligibility", execution_policy["note"])
        self.assertIn("distinct from promotion Replay", execution_policy["note"])

        replay_shadow_policy = rows["REPLAY_SHADOW_SEPARATION_POLICY"]
        self.assertIn("replay_fixed_historical_evaluation_not_shadow_selection", replay_shadow_policy["payload"])
        self.assertIn("shadow_realtime_promoted_model_selection", replay_shadow_policy["payload"])
        self.assertIn("must not call execution_shadow_cycle_selection", replay_shadow_policy["note"])

        shadow_component = rows["EXECUTION_SHADOW_RUNTIME_COMPONENT"]
        self.assertEqual(shadow_component["payload"], "execution_shadow_runtime_component")
        self.assertIn("not used by promotion Replay", shadow_component["note"])
        self.assertIn("no broker/order/account or active-pointer mutation authority", shadow_component["note"])

        shadow_evidence = rows["EXECUTION_SHADOW_MODEL_RUNTIME_EVIDENCE"]
        self.assertEqual(shadow_evidence["payload"], "execution_shadow_model_runtime_evidence")
        self.assertIn("cannot authorize orders", shadow_evidence["note"])

        c08_capacity = rows["EXECUTION_C08_CAPACITY_SIMULATION"]
        self.assertEqual(c08_capacity["payload"], "execution_c08_capacity_simulation")
        self.assertIn("Side-effect-free estimate", c08_capacity["note"])
        self.assertIn("no provider calls", c08_capacity["note"])

        shadow_policy = rows["SHADOW_RUNTIME_COMPONENT_POLICY"]
        self.assertIn("c08_model_group_shadow_comparison_intraday_component", shadow_policy["payload"])
        self.assertIn("not_replay", shadow_policy["payload"])
        self.assertIn("active_model_only_trading_authority", shadow_policy["payload"])
        self.assertIn("one_active_three_stable_wingmen_two_rotating_challengers", shadow_policy["payload"])
        self.assertIn("probation_uses_one_stable_wingman_slot", shadow_policy["payload"])
        self.assertIn("C08 Model Group Shadow Comparison", shadow_policy["note"])
        self.assertIn("capacity-gated", shadow_policy["note"])

        live_pause = rows["LIVE_RUNTIME_HISTORICAL_MODEL_TASK_PAUSE_POLICY"]
        self.assertIn("live_runtime_pauses_historical_model_tasks", live_pause["payload"])
        self.assertIn("c08_capacity_measured_without_historical_training_load", live_pause["payload"])
        self.assertIn("live_runtime_historical_model_tasks_paused", live_pause["note"])

        write_policy = rows["EXECUTION_ACTIVE_MODEL_CONFIG_WRITE_POLICY"]
        self.assertIn("valid_shadow_cycle_selection_required", write_policy["payload"])
        self.assertIn("rollback_ref_required", write_policy["payload"])

    def test_option_chain_source_shared_names_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        review = rows["MANAGER_OPTION_CHAIN_STATE_SOURCE_ACQUISITION_REVIEW"]
        self.assertEqual(review["kind"], "artifact_type")
        self.assertEqual(review["payload"], "manager_option_chain_state_source_acquisition_review")
        self.assertIn("option_chain_source_acquisition.py", review["path"])
        self.assertIn("broker execution", review["note"])

        policy = rows["OPTION_CHAIN_SOURCE_ACQUISITION_POLICY"]
        self.assertEqual(policy["payload"], "target_option_chain_state_source_acquisition")
        self.assertIn("policy_ref", policy["applies_to"])
        self.assertIn("historical provider acquisition", policy["note"])

        retry = rows["OPTION_CHAIN_SOURCE_RETRY_POLICY"]
        self.assertEqual(retry["payload"], "target_option_chain_state_source_retry")
        self.assertIn("Retry-policy token", retry["note"])

        request_template = rows["OPTION_CHAIN_SOURCE_REQUEST_ID_TEMPLATE"]
        self.assertEqual(
            request_template["payload"],
            "mgrreq_option_chain_window_<symbol>_<fold_start_month>_<window_date>_<hhmm>",
        )
        self.assertIn("provider run ids", request_template["note"])

        stage = rows["OPTION_CHAIN_SOURCE_STAGE_ID"]
        self.assertEqual(stage["payload"], "layer_03_target_state_vector.option_chain_data_acquisition")
        self.assertIn("stage_id", stage["applies_to"])

    def test_post_replay_attribution_shared_names_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        event_interpretation = rows["EVENT_INTERPRETATION"]
        self.assertEqual(event_interpretation["kind"], "artifact_type")
        self.assertEqual(event_interpretation["payload"], "event_interpretation")
        self.assertIn("schema_version", event_interpretation["note"])

        event_interpretation_policy = rows["EVENT_INTERPRETATION_STANDARD_POLICY"]
        self.assertEqual(event_interpretation_policy["payload"], "event_interpretation_standard")
        self.assertIn("policy_ref", event_interpretation_policy["applies_to"])
        self.assertIn("unversioned", event_interpretation_policy["note"])

        event_sql_inputs = rows["LAYER_TEN_EVENT_FEED_SQL_INPUTS"]
        self.assertIn("trading_data.feed_03_alpaca_news", event_sql_inputs["payload"])
        self.assertIn("event_sql_inputs", event_sql_inputs["applies_to"])
        self.assertIn("no provider calls", event_sql_inputs["note"])

        event_sql_field = rows["EVENT_FEED_SQL_INPUTS"]
        self.assertEqual(event_sql_field["kind"], "field")
        self.assertEqual(event_sql_field["payload"], "event_feed_sql_inputs")
        self.assertIn("m10_event_risk_governor_data_acquisition", event_sql_field["applies_to"])

        zero_sql_status = rows["LAYER_TEN_DETECTOR_STATUS_SKIPPED_ZERO_SQL_BAR_ROWS"]
        self.assertEqual(zero_sql_status["kind"], "status_value")
        self.assertEqual(zero_sql_status["payload"], "skipped_zero_sql_bar_rows")

        triage_receipt = rows["MANAGER_POST_REPLAY_FAILURE_TRIAGE_RECEIPT"]
        self.assertEqual(triage_receipt["payload"], "post_replay_failure_triage_receipt")
        self.assertIn("not Layer 10", triage_receipt["note"])

        triage_row = rows["MANAGER_POST_REPLAY_FAILURE_TRIAGE_ROW"]
        self.assertEqual(triage_row["payload"], "post_replay_failure_triage_row")

        layer_ten_receipt = rows["MANAGER_POST_REPLAY_LAYER_10_EVENT_ATTRIBUTION_RECEIPT"]
        self.assertEqual(layer_ten_receipt["payload"], "post_replay_layer_10_event_attribution_receipt")
        self.assertIn("provider calls", layer_ten_receipt["note"])

        layer_ten_row = rows["MANAGER_POST_REPLAY_LAYER_10_EVENT_ATTRIBUTION_ROW"]
        self.assertEqual(layer_ten_row["payload"], "model_10_event_risk_governor_event_attribution_row")
        self.assertIn("event_interpretation", layer_ten_row["applies_to"])

        focus_row = rows["MANAGER_POST_REPLAY_LAYER_10_EVENT_FOCUS_PROPOSAL_ROW"]
        self.assertEqual(focus_row["payload"], "model_10_event_risk_governor_event_focus_proposal")
        self.assertIn("event-strategy-promotion-review", focus_row["applies_to"])
        self.assertIn("model_group.layer_10_event_attribution", focus_row["applies_to"])
        self.assertIn("temporal_attention_pool", focus_row["applies_to"])

        temporal_attention_candidate = rows["MANAGER_POST_REPLAY_TEMPORAL_ATTENTION_CANDIDATE_ROW"]
        self.assertEqual(
            temporal_attention_candidate["payload"],
            "model_10_event_risk_governor_temporal_attention_candidate",
        )
        self.assertIn("temporal_attention_pool", temporal_attention_candidate["applies_to"])

        occurrence_scan = rows["MANAGER_POST_REPLAY_EVENT_FAMILY_OCCURRENCE_SCAN_ROW"]
        self.assertEqual(
            occurrence_scan["payload"],
            "model_10_event_risk_governor_event_family_occurrence_scan_row",
        )

        bias_packet = rows["MANAGER_POST_REPLAY_EVENT_FAMILY_BIAS_ASSOCIATION_PACKET"]
        self.assertEqual(
            bias_packet["payload"],
            "model_10_event_risk_governor_event_family_bias_association_packet",
        )
        self.assertIn("event-strategy-promotion-review", bias_packet["applies_to"])

        strategy_review = rows["EVENT_STRATEGY_PROMOTION_REVIEW"]
        self.assertEqual(strategy_review["payload"], "event_strategy_promotion_review")
        self.assertIn("agent_review", strategy_review["applies_to"])

        attention_pool_entry = rows["MANAGER_POST_REPLAY_TEMPORAL_ATTENTION_POOL_ENTRY"]
        self.assertEqual(
            attention_pool_entry["payload"],
            "model_10_event_risk_governor_temporal_attention_pool_entry",
        )
        self.assertIn("layer_4_state_overlay_candidate", attention_pool_entry["applies_to"])

        runtime_surfaces = rows["MANAGER_POST_REPLAY_ATTRIBUTION_RUNTIME_SURFACES"]
        self.assertIn("post_replay_failure_triage_runs", runtime_surfaces["payload"])
        self.assertIn("event_focus_proposals.jsonl", runtime_surfaces["payload"])
        self.assertIn("temporal_attention_candidate_pool.jsonl", runtime_surfaces["payload"])
        self.assertIn("event_family_occurrence_scan.jsonl", runtime_surfaces["payload"])
        self.assertIn("event_family_bias_association_packets.jsonl", runtime_surfaces["payload"])
        self.assertIn("event_strategy_promotion_reviews.jsonl", runtime_surfaces["payload"])
        self.assertIn("accepted_temporal_attention_pool_entries.jsonl", runtime_surfaces["payload"])
        self.assertIn("model_group.layer_10_event_attribution", runtime_surfaces["payload"])

        review_defaults = rows["MANAGER_LAYER_10_EVENT_STRATEGY_REVIEW_DEFAULTS"]
        self.assertIn("codex_model=gpt-5.5", review_defaults["payload"])
        self.assertIn("timeout_seconds=900", review_defaults["payload"])
        self.assertIn("max_agent_review_packets=3", review_defaults["payload"])
        self.assertIn("--local-fallback-review", review_defaults["payload"])

        focus_count = rows["EVENT_FOCUS_PROPOSAL_COUNT"]
        self.assertEqual(focus_count["kind"], "field")
        self.assertEqual(focus_count["payload"], "event_focus_proposal_count")

        focus_review_gate = rows["EVENT_FOCUS_PROPOSAL_REVIEW_GATE"]
        self.assertEqual(focus_review_gate["payload"], "event_focus_proposal_review_gate")
        self.assertIn("event-strategy-promotion-review", focus_review_gate["applies_to"])
        self.assertNotIn("event attention pool", focus_review_gate["note"])

        accepted_mutation_flag = rows["ACCEPTED_EVENT_POOL_MUTATION_PERFORMED"]
        self.assertEqual(accepted_mutation_flag["payload"], "accepted_event_pool_mutation_performed")
        self.assertIn("safety_flag", accepted_mutation_flag["applies_to"])

        temporal_mutation_flag = rows["TEMPORAL_ATTENTION_POOL_MUTATION_PERFORMED"]
        self.assertEqual(temporal_mutation_flag["payload"], "temporal_attention_pool_mutation_performed")
        self.assertIn("safety_flag", temporal_mutation_flag["applies_to"])

        field_payloads = {
            "TEMPORAL_ATTENTION_CANDIDATE_COUNT": "temporal_attention_candidate_count",
            "EVENT_FAMILY_OCCURRENCE_SCAN_ROW_COUNT": "event_family_occurrence_scan_row_count",
            "EVENT_FAMILY_BIAS_ASSOCIATION_PACKET_COUNT": "event_family_bias_association_packet_count",
            "EVENT_STRATEGY_PROMOTION_REVIEW_COUNT": "event_strategy_promotion_review_count",
            "ACCEPTED_TEMPORAL_ATTENTION_POOL_ENTRY_COUNT": "accepted_temporal_attention_pool_entry_count",
            "EVENT_STRATEGY_PROMOTION_REVIEW_STATUS": "event_strategy_promotion_review_status",
            "EVENT_LIFECYCLE_STAGE": "event_lifecycle_stage",
            "STATE_SIGNAL_TYPE": "state_signal_type",
            "LAYER_4_STATE_OVERLAY": "layer_4_state_overlay",
            "EVENT_RELEASE_PHASE": "event_release_phase",
            "EVENT_RELEASE_PHASE_COUNTS": "event_release_phase_counts",
            "EVENT_LIFECYCLE_STAGE_COUNTS": "event_lifecycle_stage_counts",
            "STATE_SIGNAL_TYPE_COUNTS": "state_signal_type_counts",
            "LAYER_4_STATE_OVERLAY_COUNTS": "layer_4_state_overlay_counts",
            "IMPACT_EXPOSURE_TIME": "impact_exposure_time",
            "IMPACT_ONSET_BASIS": "impact_onset_basis",
            "IMPACT_SCOPE_TYPE": "impact_scope_type",
            "IMPACT_NORMALIZED_SEVERITY_SCORE": "impact_normalized_severity_score",
            "IMPACT_SEVERITY_BASIS": "impact_severity_basis",
            "IMPACT_ONSET_STATUS": "impact_onset_status",
            "IMPACT_SEVERITY_STATUS": "impact_severity_status",
            "EVENT_TEMPORAL_FORM": "event_temporal_form",
            "EVENT_SCHEDULE_TYPE": "event_schedule_type",
            "EVENT_INSTANCE_OBSERVATION_ROLE": "event_instance_observation_role",
            "EVENT_FAMILY_PRIOR_ROLE": "event_family_prior_role",
            "LAYER_4_PROJECTION_TYPE": "layer_4_projection_type",
            "EVENT_FAMILY_IMPACT_PARAMETERIZATION": "event_family_impact_parameterization",
            "EVENT_TEMPORAL_FORM_COUNTS": "event_temporal_form_counts",
            "EVENT_SCHEDULE_TYPE_COUNTS": "event_schedule_type_counts",
            "EVENT_INSTANCE_OBSERVATION_ROLE_COUNTS": "event_instance_observation_role_counts",
            "LAYER_4_PROJECTION_TYPE_COUNTS": "layer_4_projection_type_counts",
        }
        for key, payload in field_payloads.items():
            self.assertEqual(rows[key]["kind"], "field")
            self.assertEqual(rows[key]["payload"], payload)

        event_focus_proposals_ref = rows["EVENT_FOCUS_PROPOSALS_REF"]
        self.assertEqual(event_focus_proposals_ref["kind"], "path_field")
        self.assertEqual(event_focus_proposals_ref["payload"], "event_focus_proposals_ref")
        self.assertIn("model_group_evaluation", event_focus_proposals_ref["applies_to"])

        layer_ten_event_focus_proposals_ref = rows["LAYER_10_EVENT_FOCUS_PROPOSALS_REF"]
        self.assertEqual(
            layer_ten_event_focus_proposals_ref["payload"],
            "layer_10_event_focus_proposals_ref",
        )
        self.assertIn("dashboard_task_timeline", layer_ten_event_focus_proposals_ref["applies_to"])

        path_field_payloads = {
            "TEMPORAL_ATTENTION_CANDIDATE_POOL_REF": "temporal_attention_candidate_pool_ref",
            "EVENT_FAMILY_OCCURRENCE_SCAN_REF": "event_family_occurrence_scan_ref",
            "EVENT_FAMILY_BIAS_ASSOCIATION_PACKETS_REF": "event_family_bias_association_packets_ref",
            "EVENT_STRATEGY_PROMOTION_REVIEWS_REF": "event_strategy_promotion_reviews_ref",
            "ACCEPTED_TEMPORAL_ATTENTION_POOL_REF": "accepted_temporal_attention_pool_ref",
        }
        for key, payload in path_field_payloads.items():
            self.assertEqual(rows[key]["kind"], "path_field")
            self.assertEqual(rows[key]["payload"], payload)

        status_payloads = {
            "EVENT_LIFECYCLE_STAGE_PRE_RELEASE_RISK_STATE": "pre_release_risk_state",
            "EVENT_LIFECYCLE_STAGE_POST_RELEASE_IMPACT_STATE": "post_release_impact_state",
            "STATE_SIGNAL_TYPE_RISK_STATE": "risk_state",
            "STATE_SIGNAL_TYPE_IMPACT_STATE": "impact_state",
            "LAYER_4_STATE_OVERLAY_EVENT_PRE_RELEASE_RISK_STATE_CHANGE": "event_pre_release_risk_state_change",
            "LAYER_4_STATE_OVERLAY_EVENT_POST_RELEASE_IMPACT_STATE": "event_post_release_impact_state",
            "EVENT_RELEASE_PHASE_PRE_RELEASE": "pre_release",
            "EVENT_RELEASE_PHASE_POST_RELEASE": "post_release",
        }
        for key, payload in status_payloads.items():
            self.assertEqual(rows[key]["kind"], "status_value")
            self.assertEqual(rows[key]["payload"], payload)

        triage_script = rows["MODEL_GROUP_POST_REPLAY_FAILURE_TRIAGE_RUN"]
        self.assertEqual(triage_script["kind"], "script")
        self.assertIn("run_model_group_post_replay_attribution.py", triage_script["path"])

        layer_ten_script = rows["MODEL_GROUP_LAYER_10_EVENT_ATTRIBUTION_RUN"]
        self.assertEqual(layer_ten_script["kind"], "script")
        self.assertIn("run_model_group_layer_ten_attribution.py", layer_ten_script["path"])
        self.assertIn("event_strategy_promotion_review", layer_ten_script["applies_to"])

        self.assertNotIn("event_interpretation_v1", {row["payload"] for row in rows.values()})

    def test_event_family_impact_window_backtest_names_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        backtest_artifact = rows["EVENT_FAMILY_IMPACT_WINDOW_BACKTEST"]
        self.assertEqual(backtest_artifact["kind"], "artifact_type")
        self.assertEqual(backtest_artifact["payload"], "event_family_impact_window_backtest")
        self.assertIn("real_input_backtest", backtest_artifact["applies_to"])
        self.assertIn("reviewed real-input", backtest_artifact["note"])

        real_input_evidence = rows["EVENT_FAMILY_IMPACT_WINDOW_REAL_INPUT_BACKTEST_20260610"]
        self.assertEqual(real_input_evidence["kind"], "artifact_type")
        self.assertEqual(real_input_evidence["payload"], "event_family_impact_window_real_input_backtest")
        self.assertIn("event_family_impact_window_real_input_backtest_20260610", real_input_evidence["path"])
        self.assertIn("review_ready_not_promotion_approved", real_input_evidence["applies_to"])
        self.assertIn("SQL-retained", real_input_evidence["note"])

        generic_runner = rows["MODEL_10_EVENT_FAMILY_IMPACT_WINDOW_BACKTEST_BUILD"]
        self.assertEqual(generic_runner["kind"], "script")
        self.assertIn("build_event_family_impact_window_backtest.py", generic_runner["path"])
        self.assertIn("real_input_backtest", generic_runner["applies_to"])

        real_input_runner = rows["MODEL_10_EVENT_FAMILY_IMPACT_WINDOW_REAL_INPUT_BACKTEST_BUILD"]
        self.assertEqual(real_input_runner["kind"], "script")
        self.assertIn("build_event_family_impact_window_real_input_backtest.py", real_input_runner["path"])
        self.assertIn("event_family_impact_window_real_input_backtest", real_input_runner["payload"])
        self.assertIn("review_ready_not_promotion_approved", real_input_runner["applies_to"])

        replay_overlay = rows["EVENT_FAMILY_IMPACT_WINDOW_REPLAY_OVERLAY_20260610"]
        self.assertEqual(replay_overlay["kind"], "artifact_type")
        self.assertEqual(replay_overlay["payload"], "event_family_impact_window_replay_overlay")
        self.assertIn("event_family_impact_window_replay_20260610", replay_overlay["path"])
        self.assertIn("replay_overlay_evidence_not_promotion_approval", replay_overlay["applies_to"])

        replay_summary = rows["EVENT_FAMILY_IMPACT_WINDOW_REPLAY_OVERLAY_SUMMARY"]
        self.assertEqual(replay_summary["kind"], "artifact_type")
        self.assertEqual(replay_summary["payload"], "event_family_impact_window_replay_overlay_summary")
        self.assertIn("event_family_impact_window_replay_summary.json", replay_summary["applies_to"])

        replay_row = rows["EVENT_FAMILY_IMPACT_WINDOW_REPLAY_OVERLAY_ROW"]
        self.assertEqual(replay_row["kind"], "artifact_type")
        self.assertEqual(replay_row["payload"], "event_family_impact_window_replay_overlay_row")
        self.assertIn("decision_event_overlay_rows.jsonl", replay_row["applies_to"])
        self.assertIn("Uncalibrated", replay_row["note"])

        replay_runner = rows["MODEL_10_EVENT_FAMILY_IMPACT_WINDOW_REPLAY_OVERLAY_BUILD"]
        self.assertEqual(replay_runner["kind"], "script")
        self.assertIn("build_event_family_impact_window_replay.py", replay_runner["path"])
        self.assertIn("event_family_impact_window_replay_overlay", replay_runner["applies_to"])

        family_terms = {
            "BREAKING_NEWS_SHOCK_EVENT_FAMILY": "breaking_news_shock",
            "CPI_INFLATION_RELEASE_EVENT_FAMILY": "cpi_inflation_release",
            "TRIPLE_WITCHING_CALENDAR_EVENT_FAMILY": "triple_witching_calendar",
        }
        for key, payload in family_terms.items():
            self.assertEqual(rows[key]["kind"], "term")
            self.assertEqual(rows[key]["payload"], payload)
            self.assertIn("event_family_key", rows[key]["applies_to"])

        self.assertEqual(rows["EVENT_FAMILY_KEY"]["kind"], "field")
        self.assertEqual(rows["EVENT_FAMILY_KEY"]["payload"], "event_family_key")
        self.assertEqual(rows["EVENT_WINDOW_POLICY"]["kind"], "field")
        self.assertEqual(rows["EVENT_WINDOW_POLICY"]["payload"], "window_policy")

        window_policies = {
            "CALIBRATED_IMPACT_WINDOW_POLICY": "calibrated_impact_window",
            "KEYWORD_SQL_OBSERVATION_DAY_UNVALIDATED_POLICY": "keyword_sql_observation_day_unvalidated",
        }
        for key, payload in window_policies.items():
            self.assertEqual(rows[key]["kind"], "status_value")
            self.assertEqual(rows[key]["payload"], payload)
            self.assertEqual(rows[key]["applies_to"], "window_policy")

    def test_layer_10_fold_completion_names_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        all_family_backtest = rows["EVENT_FAMILY_IMPACT_WINDOW_ALL_FAMILY_REAL_INPUT_BACKTEST_20260610"]
        self.assertEqual(all_family_backtest["kind"], "artifact_type")
        self.assertEqual(all_family_backtest["payload"], "event_family_impact_window_all_family_real_input_backtest")
        self.assertIn("event_family_impact_window_all_family_real_input_backtest_20260610", all_family_backtest["path"])

        all_family_replay = rows["EVENT_FAMILY_IMPACT_WINDOW_ALL_FAMILY_REPLAY_OVERLAY_20260610"]
        self.assertEqual(all_family_replay["kind"], "artifact_type")
        self.assertEqual(all_family_replay["payload"], "event_family_impact_window_all_family_replay_overlay")
        self.assertIn("event_family_impact_window_all_family_replay_20260610", all_family_replay["path"])

        fold_artifact = rows["EVENT_RISK_GOVERNOR_LAYER_10_FOLD_COMPLETION_20260610"]
        self.assertEqual(fold_artifact["kind"], "artifact_type")
        self.assertEqual(fold_artifact["payload"], "layer_10_fold_completion")
        self.assertIn("layer_10_fold_completion_20260610", fold_artifact["path"])
        self.assertIn("review_ready_not_promotion_approved", fold_artifact["applies_to"])
        self.assertIn("production-route review dispositions", fold_artifact["note"])

        summary = rows["EVENT_RISK_GOVERNOR_LAYER_10_FOLD_COMPLETION_SUMMARY"]
        self.assertEqual(summary["kind"], "artifact_type")
        self.assertEqual(summary["payload"], "layer_10_fold_completion_summary")
        self.assertIn("layer_10_fold_completion_summary.json", summary["applies_to"])

        gate_matrix = rows["EVENT_RISK_GOVERNOR_LAYER_10_FAMILY_GATE_MATRIX"]
        self.assertEqual(gate_matrix["kind"], "artifact_type")
        self.assertEqual(gate_matrix["payload"], "layer_10_family_gate_matrix")
        self.assertIn("layer_10_family_gate_matrix.csv", gate_matrix["applies_to"])

        all_family_runner = rows["MODEL_10_EVENT_FAMILY_IMPACT_WINDOW_ALL_FAMILY_REAL_INPUT_BACKTEST_BUILD"]
        self.assertEqual(all_family_runner["kind"], "script")
        self.assertIn("build_event_family_impact_window_all_family_real_input_backtest.py", all_family_runner["path"])
        self.assertIn("event_family_impact_window_all_family_real_input_backtest", all_family_runner["applies_to"])

        runner = rows["MODEL_10_EVENT_RISK_GOVERNOR_LAYER_10_FOLD_COMPLETION_BUILD"]
        self.assertEqual(runner["kind"], "script")
        self.assertIn("build_layer_10_fold_completion.py", runner["path"])
        self.assertIn("fold_completion.py", runner["path"])
        self.assertIn("layer_10_fold_completion", runner["applies_to"])

        fold_fields = {
            "CROSS_FOLD_STABILITY_ROLE": "cross_fold_stability_role",
            "FOCUS_POOL_STATUS": "focus_pool_status",
            "PRODUCTION_COMPLETION_STATUS": "production_completion_status",
            "PRODUCTION_ROUTE_DECISION": "production_route_decision",
            "PRODUCTION_ROUTE_REVIEW_STATUS": "production_route_review_status",
        }
        for key, payload in fold_fields.items():
            self.assertEqual(rows[key]["kind"], "field")
            self.assertEqual(rows[key]["payload"], payload)
            self.assertIn("layer_10_fold_completion", rows[key]["applies_to"])

        fold_status_values = {
            "LAYER_10_CROSS_FOLD_STABILITY_POST_FOCUS_POOL_MONITORING": "post_focus_pool_monitoring_not_focus_pool_prerequisite",
            "LAYER_10_FOCUS_POOL_ACCEPTED_TEMPORAL_ATTENTION": "accepted_temporal_attention_focus_pool",
            "LAYER_10_FOCUS_POOL_DEFERRED_TEMPORAL_ATTENTION": "deferred_from_temporal_attention_focus_pool",
            "LAYER_10_FOCUS_POOL_REJECTED_TEMPORAL_ATTENTION": "rejected_from_temporal_attention_focus_pool",
            "LAYER_10_PRODUCTION_COMPLETION_ROUTE_REVIEW_COMPLETE": "production_route_review_complete",
            "LAYER_10_PRODUCTION_ROUTE_DECISION_APPROVE_FOCUS_POOL_DEFER_STRONGER_MODEL_USE": "approve_focus_pool_entry_defer_stronger_model_use",
            "LAYER_10_PRODUCTION_ROUTE_DECISION_APPROVE_FOCUS_POOL_RISK_CONTROL_ONLY": "approve_focus_pool_entry_risk_control_only",
            "LAYER_10_PRODUCTION_ROUTE_DECISION_DEFER_INCOMPLETE_WORKFLOW": "defer_incomplete_layer10_workflow",
            "LAYER_10_PRODUCTION_ROUTE_DECISION_REJECT_CURRENT_DEFINITION_NEEDS_REWORK": "reject_current_definition_needs_rework",
            "LAYER_10_PRODUCTION_ROUTE_REVIEW_AGENT_COMPLETE": "agent_review_complete",
            "LAYER_10_PRODUCTION_ROUTE_REVIEW_BLOCKED_MISSING_PACKET_OR_PRECONDITION": "agent_review_blocked_missing_packet_or_precondition",
            "LAYER_10_PRODUCTION_ROUTE_REVIEW_BLOCKED_UNVALIDATED_IMPACT_WINDOW": "agent_review_blocked_unvalidated_impact_window",
            "LAYER_10_PRODUCTION_ROUTE_REVIEW_DEFERRED_INCOMPLETE_WORKFLOW": "agent_review_deferred_incomplete_layer10_workflow",
        }
        for key, payload in fold_status_values.items():
            self.assertEqual(rows[key]["kind"], "status_value")
            self.assertEqual(rows[key]["payload"], payload)

    def test_layer_4_focus_pool_and_layer_5_event_feature_policy_names_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        focus_pool = rows["LAYER_04_FOCUS_POOL_INPUTS_20260610"]
        self.assertEqual(focus_pool["kind"], "artifact_type")
        self.assertEqual(focus_pool["payload"], "layer_04_focus_pool_inputs")
        self.assertIn("layer_04_focus_pool_inputs_20260610", focus_pool["path"])
        self.assertIn("layer_10_focus_pool_inputs", focus_pool["applies_to"])
        self.assertIn("review_ready_not_promotion_approved", focus_pool["applies_to"])

        self.assertEqual(rows["LAYER_04_FOCUS_POOL_INPUT_ROWS"]["payload"], "layer_04_focus_pool_input_rows")
        self.assertEqual(rows["LAYER_04_FOCUS_POOL_MODEL_ROWS"]["payload"], "model_04_event_failure_risk_rows")

        focus_runner = rows["MODEL_04_EVENT_FAILURE_RISK_LAYER_10_FOCUS_POOL_INPUTS_BUILD"]
        self.assertEqual(focus_runner["kind"], "script")
        self.assertIn("build_layer4_focus_pool_inputs.py", focus_runner["path"])
        self.assertIn("layer10_focus_pool_inputs.py", focus_runner["path"])
        self.assertIn("review_ready_not_promotion_approved", focus_runner["applies_to"])

        self.assertEqual(rows["LAYER4_EVENT_FEATURE_POLICY"]["payload"], "layer4_event_feature_policy")
        self.assertEqual(rows["LAYER4_EVENT_FEATURE_NAMES"]["payload"], "layer4_event_feature_names")
        self.assertEqual(rows["FEATURE_CONSUMPTION_CONTRACT"]["payload"], "feature_consumption_contract")
        self.assertIn(
            "consume_reviewed_layer4_event_failure_risk_vector_when_present",
            rows["ALPHA_CONFIDENCE_LAYER4_EVENT_FEATURE_CONSUMPTION_POLICY"]["payload"],
        )
        self.assertIn("formal_training_input", rows["ALPHA_CONFIDENCE_LAYER4_EVENT_FEATURE_CONSUMPTION_POLICY"]["payload"])
        self.assertNotIn("baseline_without_layer4_event_features", rows["ALPHA_CONFIDENCE_LAYER4_EVENT_FEATURE_CONSUMPTION_POLICY"]["payload"])
        self.assertEqual(
            rows["LAYER_05_LAYER4_EVENT_FEATURE_POLICY_CONSUME_REVIEWED_WHEN_PRESENT"]["payload"],
            "consume_reviewed_layer4_event_failure_risk_vector_when_present",
        )
        self.assertEqual(rows["LAYER_05_FEATURE_CONSUMPTION_FORMAL_TRAINING_INPUT"]["payload"], "formal_training_input")

        retired_contrast_keys = {
            "ALPHA_CONFIDENCE_EVENT_CONDITIONED_ALPHA_CONTRAST_POLICY",
            "BASELINE_ROLE",
            "BASELINE_WITHOUT_LAYER4_EVENT_FEATURES",
            "FORMAL_TRAINING_ROUTE",
            "LAYER_05_DIAGNOSTIC_SCOPE",
            "LAYER_05_DIAGNOSTIC_SCOPE_NOT_PROMOTION",
            "LAYER_05_EVENT_CONDITIONED_AFTER_COST_ALPHA_MODEL",
            "LAYER_05_EVENT_CONDITIONED_ALPHA_CONTRAST_20260610",
            "LAYER_05_EVENT_CONDITIONED_ALPHA_CONTRAST_PREDICTIONS",
            "LAYER_05_EVENT_CONDITIONED_ALPHA_CONTRAST_SUMMARY",
            "LAYER_05_EVENT_CONDITIONED_BASELINE_ALPHA_MODEL",
            "LAYER_05_FEATURE_CONSUMPTION_EVALUATION_ONLY_NOT_TRAINING_ROUTE",
            "LAYER_05_FORMAL_TRAINING_ROUTE_CONSUME_LAYER4_EVENT_FAILURE_RISK_VECTOR",
            "LAYER_05_LABEL_SOURCE",
            "LAYER_05_LABEL_SOURCE_LAYER10_REPLAY_EXCESS_RETURN",
            "MODEL_05_ALPHA_CONFIDENCE_EVENT_CONDITIONED_ALPHA_CONTRAST_BUILD",
            "SOURCE_DECISION_ID",
        }
        self.assertFalse(retired_contrast_keys & rows.keys())

    def test_event_family_remaining_acceptance_names_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["ACCEPTANCE_STATUS"]["kind"], "field")
        self.assertEqual(rows["ACCEPTANCE_STATUS"]["payload"], "acceptance_status")
        self.assertEqual(rows["ACCEPTED_CURRENT_USE"]["kind"], "field")
        self.assertEqual(rows["ACCEPTED_CURRENT_USE"]["payload"], "accepted_current_use")

        status_values = {
            "EVENT_FAMILY_ACCEPTANCE_BLOCKED_MISSING_LIQUIDITY_EVIDENCE": "blocked_missing_liquidity_evidence",
            "EVENT_FAMILY_ACCEPTANCE_BLOCKED_MISSING_PIT_EXPECTATION_OR_COMPARABLE_BASELINE": "blocked_missing_pit_expectation_or_comparable_baseline",
            "EVENT_FAMILY_ACCEPTANCE_BLOCKED_MISSING_RESIDUAL_DEFINITION": "blocked_missing_residual_definition",
            "EVENT_FAMILY_ACCEPTANCE_PACKET_REQUIRED_HIGH_PRIORITY": "packet_required_high_priority",
            "EVENT_FAMILY_ACCEPTANCE_PACKET_REQUIRED_NORMAL_PRIORITY": "packet_required_normal_priority",
            "EVENT_FAMILY_ACCEPTANCE_RISK_ONLY_CANDIDATE_PENDING_CANONICAL_EVIDENCE": "risk_only_candidate_pending_canonical_evidence",
            "EVENT_FAMILY_ACCEPTANCE_RISK_ONLY_SCOUTING_UNDERPOWERED": "risk_only_scouting_underpowered",
            "EVENT_FAMILY_CURRENT_USE_MACRO_RISK_SURPRISE_CONTROL_PENDING_CANONICAL_TE_HISTORY": "macro_risk_surprise_control_pending_canonical_te_history",
        }
        for key, payload in status_values.items():
            self.assertEqual(rows[key]["kind"], "status_value")
            self.assertEqual(rows[key]["payload"], payload)
            self.assertIn("event_family_remaining_acceptance", rows[key]["applies_to"])

        registry_text = Path("scripts/registry/current.csv").read_text(encoding="utf-8")
        self.assertNotIn("risk_only_candidate_temporary_evidence", registry_text)
        self.assertNotIn("temporary_macro_risk_surprise_evidence_pending_canonical_te_history", registry_text)

    def test_sql_output_table_inventory_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        expected_tables = {
            "M01_MARKET_REGIME_DATA_ACQUISITION_TABLE": "trading_data.m01_market_regime_data_acquisition",
            "M01_MARKET_REGIME_FEATURE_GENERATION_TABLE": "trading_data.m01_market_regime_feature_generation",
            "M01_MARKET_REGIME_MODEL_GENERATION_TABLE": "trading_model.m01_market_regime_model_generation",
            "M01_MARKET_REGIME_MODEL_GENERATION_EXPLAINABILITY_TABLE": "trading_model.m01_market_regime_model_generation_explainability",
            "M01_MARKET_REGIME_MODEL_GENERATION_DIAGNOSTICS_TABLE": "trading_model.m01_market_regime_model_generation_diagnostics",
            "M02_SECTOR_CONTEXT_DATA_ACQUISITION_TABLE": "trading_data.m02_sector_context_data_acquisition",
            "M09_OPTION_EXPRESSION_CONTRACT_PATH_TABLE": "trading_data.m09_option_expression_data_acquisition_contract_path",
            "EVALUATION_REPLAY_CONTRACT_TABLE": "trading_evaluation.replay_contract",
            "EVALUATION_REPLAY_DATASET_PREPARATION_TABLE": "trading_evaluation.replay_dataset_preparation",
            "EVALUATION_REPLAY_DATASET_FREEZE_TABLE": "trading_evaluation.replay_dataset_freeze",
            "EVALUATION_REPLAY_SOURCE_COVERAGE_TABLE": "trading_evaluation.replay_source_coverage",
            "EVALUATION_REPLAY_EXECUTION_RUN_TABLE": "trading_evaluation.replay_execution_run",
            "EVALUATION_REPLAY_DECISION_TABLE": "trading_evaluation.replay_decision",
            "EVALUATION_REPLAY_PROGRESS_TABLE": "trading_evaluation.replay_progress",
            "EVALUATION_FOLD_SETTLEMENT_RUN_TABLE": "trading_evaluation.fold_settlement_run",
            "EVALUATION_FOLD_SETTLEMENT_METRIC_TABLE": "trading_evaluation.fold_settlement_metric",
            "EVALUATION_PROMOTION_ELIGIBILITY_DECISION_TABLE": "trading_evaluation.promotion_eligibility_decision",
            "EVALUATION_PROMOTION_READINESS_RECORD_TABLE": "trading_evaluation.promotion_readiness_record",
            "EVALUATION_PROMOTED_MODEL_PARAMETER_TABLE": "trading_evaluation.promoted_model_parameter",
            "STATUS_REALTIME_TRADING_RUNTIME_TABLE": "trading_execution.status_realtime_trading_runtime",
            "STATUS_CAPABILITY_CATALOG_TABLE": "trading_execution.status_capability_catalog",
            "STATUS_REALTIME_DATA_INTERFACE_TABLE": "trading_execution.status_realtime_data_interface",
            "STATUS_BROKER_INTERFACE_TABLE": "trading_execution.status_broker_interface",
            "REALTIME_CAPTURE_CONTRACT_TABLE": "trading_execution.realtime_capture_contract",
            "REALTIME_FEATURE_SNAPSHOT_TABLE": "trading_execution.realtime_feature_snapshot",
            "REALTIME_MODEL_DECISION_INPUT_SNAPSHOT_TABLE": "trading_execution.realtime_model_decision_input_snapshot",
            "REALTIME_INPUT_COVERAGE_TABLE": "trading_execution.realtime_input_coverage",
            "REALTIME_SUBSCRIPTION_PLAN_TABLE": "trading_execution.realtime_subscription_plan",
            "REALTIME_LIVE_OBSERVE_RESULT_TABLE": "trading_execution.realtime_live_observe_result",
            "C01_INTAKE_SNAPSHOT_TABLE": "trading_execution.c01_intake_snapshot",
            "C02_ENTRY_DECISION_TABLE": "trading_execution.c02_entry_decision",
            "C03_POSITION_LIFECYCLE_DECISION_TABLE": "trading_execution.c03_position_lifecycle_decision",
            "C04_OPTION_REEXPRESSION_DECISION_TABLE": "trading_execution.c04_option_reexpression_decision",
            "C05_ORDER_INTENT_TABLE": "trading_execution.c05_order_intent",
            "C06_EXECUTION_GATE_RESULT_TABLE": "trading_execution.c06_execution_gate_result",
            "C07_FAILURE_EXPLANATION_PACKET_TABLE": "trading_execution.c07_failure_explanation_packet",
            "PERFORMANCE_MODEL_RUNTIME_EVIDENCE_TABLE": "trading_execution.performance_model_runtime_evidence",
            "C08_SHADOW_CYCLE_SELECTION_TABLE": "trading_execution.c08_shadow_cycle_selection",
            "PERFORMANCE_RUNTIME_CAPACITY_SIMULATION_TABLE": "trading_execution.performance_runtime_capacity_simulation",
            "STATUS_ACTIVE_MODEL_CONFIG_WRITE_TABLE": "trading_execution.status_active_model_config_write",
            "TRADE_ORDER_CONSTRUCTION_APPROVAL_TABLE": "trading_execution.trade_order_construction_approval",
            "TRADE_BROKER_ORDER_INTENT_TABLE": "trading_execution.trade_broker_order_intent",
            "TRADE_BROKER_ORDER_INTENT_RESULT_TABLE": "trading_execution.trade_broker_order_intent_result",
            "TRADE_RISK_CAP_TABLE": "trading_execution.trade_risk_cap",
            "PERFORMANCE_MODEL_DECISION_EFFECTIVENESS_TABLE": "trading_execution.performance_model_decision_effectiveness",
            "PERFORMANCE_MODEL_DECISION_EFFECTIVENESS_ROW_TABLE": "trading_execution.performance_model_decision_effectiveness_row",
            "C07_FAILURE_ATTRIBUTION_TABLE": "trading_execution.c07_failure_attribution",
            "PERFORMANCE_RUNTIME_MODEL_LIFECYCLE_REVIEW_TABLE": "trading_execution.performance_runtime_model_lifecycle_review",
            "TRADE_BROKER_ORDER_SUBMISSION_TABLE": "trading_execution.trade_broker_order_submission",
            "TRADE_BROKER_ORDER_STATE_TABLE": "trading_execution.trade_broker_order_state",
            "TRADE_BROKER_FILL_TABLE": "trading_execution.trade_broker_fill",
            "TRADE_ACCOUNT_STATE_SNAPSHOT_TABLE": "trading_execution.trade_account_state_snapshot",
            "TRADE_POSITION_STATE_SNAPSHOT_TABLE": "trading_execution.trade_position_state_snapshot",
            "TRADE_RECONCILIATION_RESULT_TABLE": "trading_execution.trade_reconciliation_result",
        }
        for key, payload in expected_tables.items():
            self.assertEqual(rows[key]["kind"], "sql_table")
            self.assertEqual(rows[key]["payload"], payload)
            self.assertIn("sql_table", rows[key]["applies_to"])

        policy = rows["SQL_OUTPUT_TABLE_INVENTORY_POLICY"]
        self.assertIn("schema_qualified_table_names_required", policy["payload"])
        self.assertIn("future_broker_account_tables_reserved_not_active", policy["payload"])
        self.assertIn("does not authorize live broker submission", policy["note"])
        self.assertIn("future_gated_broker_mutation", rows["TRADE_BROKER_ORDER_SUBMISSION_TABLE"]["applies_to"])
        self.assertIn("outside the active current loop", rows["TRADE_BROKER_ORDER_SUBMISSION_TABLE"]["note"])

        layer_policy = rows["SQL_LAYER_TABLE_NAMING_POLICY"]
        self.assertIn("use_mNN_domain_task_stage_sql_names", layer_policy["payload"])
        self.assertIn("old_source_feature_model_prefixes_are_migration_debt", layer_policy["payload"])
        self.assertNotIn("use_source_NN_feature_NN_model_NN_prefixes", layer_policy["payload"])

        for stale_key in {
            "ACTIVATION_RECORD_ARTIFACT",
            "DATA_SOURCES_GLOBAL_CONFIG_DEPRECATED",
            "EXECUTION_REALTIME_RUNTIME_CHECK_TIMER",
            "EARNINGS_GUIDANCE_ARTIFACT_COVERAGE_SCOUT_Q4_2025",
            "EARNINGS_GUIDANCE_ARTIFACT_COVERAGE_WITH_DOCUMENTS_Q4_2025",
        }:
            self.assertNotIn(stale_key, rows)

    def test_execution_runtime_component_graph_rows_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["EXECUTION_RUNTIME_COMPONENT"]["payload"], "execution_runtime_component")
        self.assertIn("trading-execution/docs/50_runtime_components.md", rows["EXECUTION_RUNTIME_COMPONENT"]["path"])
        self.assertEqual(rows["EXECUTION_RUNTIME_COMPONENT_GRAPH"]["payload"], "execution_runtime_component_graph")
        self.assertIn("trading-evaluation calls this graph", rows["EXECUTION_RUNTIME_COMPONENT_GRAPH"]["note"])
        self.assertEqual(rows["EXECUTION_RUNTIME_COMPONENT_MANIFEST"]["payload"], "execution_runtime_component_manifest")
        self.assertIn("manifest_checksum", rows["EXECUTION_RUNTIME_COMPONENT_MANIFEST"]["applies_to"])
        self.assertEqual(rows["EXECUTION_INTAKE_SNAPSHOT"]["payload"], "execution_intake_snapshot")
        self.assertIn("does not allocate risk budget", rows["EXECUTION_INTAKE_SNAPSHOT"]["note"])
        self.assertEqual(rows["ENTRY_DECISION"]["payload"], "entry_decision")
        self.assertIn("does not call Layer 9 or Layer 10", rows["ENTRY_DECISION"]["note"])
        self.assertEqual(rows["POSITION_LIFECYCLE_DECISION"]["payload"], "position_lifecycle_decision")
        self.assertEqual(rows["OPTION_REEXPRESSION_DECISION"]["payload"], "option_reexpression_decision")
        self.assertEqual(rows["FAILURE_EXPLANATION_PACKET"]["payload"], "failure_explanation_packet")
        self.assertIn("Layer 4 feedback candidates", rows["FAILURE_EXPLANATION_PACKET"]["note"])
        self.assertEqual(rows["EXECUTION_ORDER_INTENT"]["payload"], "execution_order_intent")
        self.assertEqual(rows["SIMULATED_FILL_EVENT"]["payload"], "simulated_fill_event")

        policy = rows["EXECUTION_RUNTIME_COMPONENT_GRAPH_POLICY"]
        self.assertIn("same_components_live_and_replay_different_adapters", policy["payload"])
        self.assertIn("evaluation_calls_execution_graph", policy["payload"])
        self.assertIn("layer10_failure_explanation_only", policy["payload"])
        self.assertIn("separate_crypto_and_equity_options_accounts", policy["payload"])
        self.assertIn("no_cross_account_netting", policy["payload"])
        self.assertIn("Replay is a fixed historical evaluation mechanism", policy["note"])
        self.assertIn("shadow is a realtime execution-owned selection mechanism", policy["note"])

        self.assertEqual(rows["EXECUTION_ACCOUNT_SLEEVE"]["payload"], "execution_account_sleeve")
        self.assertIn("exactly one sleeve", rows["EXECUTION_ACCOUNT_SLEEVE"]["note"])
        self.assertEqual(rows["CRYPTO_SPOT_ACCOUNT_SLEEVE"]["payload"], "crypto_spot_account")
        self.assertIn("fixed BTC, ETH, and SOL candidate pool", rows["CRYPTO_SPOT_ACCOUNT_SLEEVE"]["note"])
        self.assertEqual(rows["EQUITY_OPTIONS_ACCOUNT_SLEEVE"]["payload"], "equity_options_account")
        self.assertIn("option re-expression", rows["EQUITY_OPTIONS_ACCOUNT_SLEEVE"]["note"])
        self.assertIn("symbols=BTC,ETH,SOL", rows["CRYPTO_SPOT_CANDIDATE_POOL_POLICY"]["payload"])
        self.assertIn("BTC-USDT,ETH-USDT,SOL-USDT", rows["CRYPTO_SPOT_CANDIDATE_POOL_POLICY"]["payload"])

    def test_agent_decision_skill_rows_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        fixed_policy = rows["AGENT_DECISION_FIXED_SKILL_POLICY"]
        self.assertIn("all_agent_decisions_require_fixed_workspace_skill", fixed_policy["payload"])
        self.assertIn("model_comparisons_require_anonymous_labels", fixed_policy["payload"])

        expected_skills = {
            "EVALUATION_PROMOTION_REVIEW_SKILL": "promotion-evaluation-review",
            "RUNTIME_MODEL_LIFECYCLE_REVIEW_SKILL": "runtime-model-lifecycle-review",
            "TARGET_CONTEXT_REVIEW_SKILL": "target-context-review",
            "SERVER_ERROR_DIAGNOSIS_SKILL": "server-error-diagnosis",
            "STORAGE_LIFECYCLE_REVIEW_SKILL": "storage-lifecycle-review",
            "FAILURE_REGISTER_REVIEW_SKILL": "failure-register-review",
            "EVENT_STRATEGY_PROMOTION_REVIEW_SKILL": "event-strategy-promotion-review",
        }
        for key, skill_name in expected_skills.items():
            self.assertEqual(rows[key]["payload"], skill_name)
            self.assertIn(f"{skill_name}/SKILL.md", rows[key]["path"])

        self.assertIn("target-context-review", rows["TARGET_LAYER2_CONTEXT_AGENT_REVIEW"]["note"])
        self.assertIn("server-error-diagnosis", rows["SERVER_WIDE_AGENT_ERROR_HANDOFF"]["note"])
        self.assertIn("storage-lifecycle-review", rows["AGENT_STORAGE_LIFECYCLE_DECISION"]["note"])
        self.assertIn("automatic repair", rows["MANAGER_FAILED_REQUEST_DECISION_GATE_POLICY"]["note"])
        self.assertIn("event-strategy-promotion-review", rows["EVENT_FAMILY_TO_LAYER_04_PROMOTION_POLICY"]["note"])

    def test_event_risk_governor_layer_policy_terms_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        layer_policy = rows["MODEL_LAYER_CONCEPTUAL_REORDER_POLICY"]
        self.assertIn("layer_04_event_failure_risk", layer_policy["payload"])
        self.assertIn("layer_05_alpha_confidence", layer_policy["payload"])
        self.assertIn("layer_06_dynamic_risk_policy", layer_policy["payload"])
        self.assertIn("layer_09_option_expression", layer_policy["payload"])
        self.assertIn("layer_10_event_risk_governor", layer_policy["payload"])

        self.assertEqual(rows["TRADING_GUIDANCE_MODEL"]["payload"], "trading_guidance_model")
        self.assertEqual(rows["TRADING_GUIDANCE_RECORD"]["payload"], "trading_guidance_record")
        self.assertEqual(rows["EVENT_RISK_GOVERNOR"]["payload"], "event_risk_governor")
        self.assertEqual(rows["EVENT_RISK_INTERVENTION"]["payload"], "event_risk_intervention")
        self.assertIn("reduce_or_flatten_review", rows["EVENT_RISK_INTERVENTION_STATUS_VALUES"]["payload"])
        self.assertIn("broker order", rows["EVENT_RISK_INTERVENTION"]["note"])
        self.assertIn("current_physical_surfaces_aligned_with_six_model_order", rows["CURRENT_PHYSICAL_MODEL_LAYER_NAME_POLICY"]["payload"])
        self.assertIn("legacy_ten_layer_surfaces_migration_source_only", rows["CURRENT_PHYSICAL_MODEL_LAYER_NAME_POLICY"]["payload"])

    def test_active_model_control_plane_registry_rows_use_stable_model_ids(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        numbered_model_pattern = re.compile(r"model_[0-9]{2}_[a-z_]+")
        stable_targets = rows["MODEL_PROMOTION_UNIFIED_TARGETS"]["payload"].split(";")
        self.assertEqual(
            stable_targets,
            [
                "background_context_model",
                "target_state_model",
                "event_state_model",
                "unified_decision_model",
                "option_expression_model",
                "residual_event_governance_model",
            ],
        )
        expected_receipt_model_sequence = [
            ("M01", "background_context_model"),
            ("M02", "target_state_model"),
            ("M03", "event_state_model"),
            ("M04", "unified_decision_model"),
            ("M05", "option_expression_model"),
            ("M06", "residual_event_governance_model"),
        ]
        receipt_entries = rows["MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS"]["payload"].split(";")
        self.assertEqual(
            [(entry.split(":", 2)[0], entry.split(":", 2)[1]) for entry in receipt_entries],
            expected_receipt_model_sequence,
        )
        self.assertEqual(len(receipt_entries), 6)
        self.assertIn("no_persisted_decision_receipt", receipt_entries[-1])

        for key in (
            "MODEL_PROMOTION_UNIFIED_TARGETS",
            "MODEL_LAYER_03_PRODUCTION_EVAL_SUBSTRATE_RECEIPT",
            "MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS",
        ):
            self.assertNotRegex(rows[key]["payload"], numbered_model_pattern)

    def test_storage_maintenance_service_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertNotIn("MANAGER_FOLD_CLEANUP_PLAN", rows)
        self.assertNotIn("MANAGER_FOLD_SQL_LOGICAL_BACKUP_PLAN", rows)
        self.assertNotIn("MANAGER_FOLD_CLEANUP_LOGICAL_BACKUP_POLICY", rows)
        self.assertNotIn("MANAGER_PLAN_FOLD_CLEANUP", rows)

        summary = rows["STORAGE_SCHEDULED_MAINTENANCE_SUMMARY"]
        self.assertEqual(summary["kind"], "artifact_type")
        self.assertEqual(summary["payload"], "storage_scheduled_maintenance_summary")
        self.assertIn("reads manager fold-state files directly", summary["note"])

        service = rows["STORAGE_MAINTENANCE_SYSTEMD_UNITS"]
        self.assertEqual(service["kind"], "systemd_unit")
        self.assertIn("trading-storage-maintenance.service", service["payload"])
        self.assertIn("trading-storage-maintenance.timer", service["payload"])

        boundary = rows["STORAGE_MAINTENANCE_BACKUP_DELETE_BOUNDARY_POLICY"]
        self.assertIn("storage_reads_manager_fold_state", boundary["payload"])
        self.assertIn("storage_executes_backup_archive_delete", boundary["payload"])
        self.assertIn("No manager backup/cleanup signal, request, or plan is required", boundary["note"])

    def test_data_feed_and_data_source_rows_are_separated(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["SEC_EDGAR"]["kind"], "provider")
        self.assertEqual(
            rows["SEC_EDGAR"]["path"],
            "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        )
        expected_current_providers = {
            "ALPACA",
            "GDELT",
            "OKX",
            "SEC_EDGAR",
            "THETADATA",
            "TRADING_ECONOMICS",
        }
        actual_providers = {key for key, row in rows.items() if row["kind"] == "provider"}
        self.assertEqual(actual_providers, expected_current_providers)
        for obsolete_provider_term in {"BEA", "BLS", "CENSUS", "FRED", "US_TREASURY_FISCAL_DATA"}:
            self.assertNotIn(obsolete_provider_term, rows)
        self.assertNotIn("GITHUB", rows)
        expected_sources = {
            "M01_MARKET_REGIME_DATA_ACQUISITION": "m01_market_regime_data_acquisition",
            "M02_SECTOR_CONTEXT_DATA_ACQUISITION": "m02_sector_context_data_acquisition",
            "M03_TARGET_STATE_VECTOR_DATA_ACQUISITION": "m03_target_state_vector_data_acquisition",
            "OPTION_CHAIN_STATE_SOURCE": "option_chain_state_source",
            "M10_EVENT_RISK_GOVERNOR_DATA_ACQUISITION": "m10_event_risk_governor_data_acquisition",
            "M09_OPTION_EXPRESSION_DATA_ACQUISITION_CONTRACT_PATH": "m09_option_expression_data_acquisition_contract_path",
        }
        expected_feeds = {
            "ALPACA_BARS": "01_feed_alpaca_bars",
            "ALPACA_LIQUIDITY": "02_feed_alpaca_liquidity",
            "ALPACA_NEWS": "03_feed_alpaca_news",
            "OKX_CRYPTO_MARKET_DATA": "04_feed_okx_crypto_market_data",
            "GDELT_NEWS": "05_feed_gdelt_news",
            "ETF_HOLDINGS": "06_feed_etf_holdings",
            "TRADING_ECONOMICS_CALENDAR_WEB": "07_feed_trading_economics_calendar_web",
            "SEC_COMPANY_FINANCIALS": "08_feed_sec_company_financials",
            "THETADATA_OPTION_SELECTION_SNAPSHOT": "09_feed_thetadata_option_selection_snapshot",
            "THETADATA_OPTION_PRIMARY_TRACKING": "10_feed_thetadata_option_primary_tracking",
            "THETADATA_OPTION_EVENT_TIMELINE": "11_feed_thetadata_option_event_timeline",
        }
        for key, payload in expected_sources.items():
            self.assertEqual(rows[key]["kind"], "data_source")
            self.assertEqual(rows[key]["payload"], payload)
            if key == "M10_EVENT_RISK_GOVERNOR_DATA_ACQUISITION":
                self.assertIn("data_source/m10_event_risk_governor_data_acquisition", rows[key]["path"])
            else:
                self.assertIn(f"data_source/{payload}", rows[key]["path"])
            self.assertNotIn("_model_inputs", rows[key]["payload"])
            self.assertNotIn("_model_inputs", rows[key]["path"])
        for key, payload in expected_feeds.items():
            self.assertEqual(rows[key]["kind"], "data_feed")
            self.assertEqual(rows[key]["payload"], payload)
            self.assertIn(f"data_feed/{payload}", rows[key]["path"])
        for row in rows.values():
            self.assertNotIn("trading-" + "source", row["path"])
            self.assertNotIn("trading-" + "derived", row["path"])
            self.assertNotIn("data_sources/", row["path"])
            self.assertNotIn("data_bundles/", row["path"])
            self.assertNotIn("source_availability", row["path"])
            self.assertNotIn("source_interfaces", row["path"])
        self.assertNotIn("MACRO_DATA", rows)
        self.assertNotIn("STOCK_ETF_EXPOSURE_BUNDLE_DEPRECATED", rows)
        self.assertNotIn("EQUITY_ABNORMAL_ACTIVITY_BUNDLE", rows)
        self.assertNotIn("EQUITY_ABNORMAL_ACTIVITY_BUNDLE_CONFIG", rows)
        for obsolete_config in {
            "01_MARKET_REGIME_MODEL_INPUTS_BUNDLE_CONFIG",
            "03_STRATEGY_SELECTION_MODEL_INPUTS_BUNDLE_CONFIG",
            "05_OPTION_EXPRESSION_MODEL_INPUTS_BUNDLE_CONFIG",
        }:
            self.assertNotIn(obsolete_config, rows)
        self.assertEqual(rows["MODEL_DECISION_HORIZON_GRID"]["payload"], "10min;1h;1D;1W")
        self.assertIn("rolling 24-hour", rows["MODEL_DECISION_HORIZON_GRID"]["note"])
        self.assertEqual(rows["TARGET_STATE_VECTOR_SYNCHRONIZED_STATE_WINDOWS"]["payload"], "model_decision_horizon_grid")
        self.assertEqual(rows["TARGET_CONTEXT_STATE_VERSION_DEFAULT"]["payload"], "target_context_state")
        self.assertEqual(
            rows["TARGET_STATE_VECTOR_WINDOW_SYNC_POLICY"]["payload"],
            "market_sector_target_blocks_must_share_identical_observation_windows",
        )
        self.assertIn("3_target_direction_score_<window>", rows["TARGET_STATE_VECTOR_DIRECTION_NEUTRAL_SCORE_FAMILIES"]["payload"])
        self.assertIn("3_tradability_score_<window>", rows["TARGET_STATE_VECTOR_DIRECTION_NEUTRAL_SCORE_FAMILIES"]["payload"])
        for expected_target_state_vector_payload in {
            "3_target_direction_score_<window>",
            "3_target_direction_strength_score_<window>",
            "3_target_trend_quality_score_<window>",
            "3_target_path_stability_score_<window>",
            "3_target_noise_score_<window>",
            "3_target_transition_risk_score_<window>",
            "3_target_state_persistence_score_<window>",
            "3_target_exhaustion_risk_score_<window>",
            "3_target_liquidity_tradability_score",
            "3_context_direction_alignment_score_<window>",
            "3_context_support_quality_score_<window>",
            "3_tradability_score_<window>",
        }:
            self.assertIn(expected_target_state_vector_payload, {row["payload"] for row in rows.values()})
        self.assertEqual(rows["MODEL_VECTOR_TAXONOMY"]["payload"], "model_vector_taxonomy")
        self.assertEqual(rows["EVENT_RISK_GOVERNOR"]["payload"], "event_risk_governor")
        self.assertEqual(rows["MODEL_10_EVENT_RISK_GOVERNOR"]["payload"], "model_10_event_risk_governor")
        self.assertEqual(rows["EVENT_CONTEXT_VECTOR"]["payload"], "event_context_vector")
        self.assertEqual(rows["EVENT_CONTEXT_VECTOR_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("price_action", rows["EVENT_CATEGORY_TYPE_VALUES"]["payload"])
        self.assertIn("false_breakout", rows["PRICE_ACTION_EVENT_TYPES"]["payload"])
        self.assertIn("layer_10_event_risk_governor_event_not_new_model_layer", rows["PRICE_ACTION_EVENT_LAYER_POLICY"]["payload"])
        self.assertIn("10_event_presence_score_<horizon>", rows["EVENT_CONTEXT_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("10_event_target_relevance_score_<horizon>", rows["EVENT_CONTEXT_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertEqual(rows["ALPHA_CONFIDENCE_MODEL"]["payload"], "alpha_confidence_model")
        self.assertEqual(rows["MODEL_05_ALPHA_CONFIDENCE"]["payload"], "model_05_alpha_confidence")
        self.assertEqual(rows["ALPHA_CONFIDENCE_VECTOR"]["payload"], "alpha_confidence_vector")
        self.assertEqual(rows["BASE_ALPHA_VECTOR"]["payload"], "base_alpha_vector")
        self.assertEqual(rows["EVENT_FAILURE_RISK_VECTOR_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("frozen_layer_10_focus_pool_contract_allowed", rows["EVENT_FAILURE_RISK_BOUNDARY_POLICY"]["payload"])
        self.assertIn("no_layer_10_event_parameter_mutation", rows["EVENT_FAILURE_RISK_BOUNDARY_POLICY"]["payload"])
        self.assertIn(
            "4_event_response_strength_score_<horizon>",
            rows["EVENT_FAILURE_RISK_VECTOR_SCORE_FAMILIES"]["payload"],
        )
        self.assertIn(
            "4_event_response_direction_score_<horizon>",
            rows["EVENT_FAILURE_RISK_VECTOR_SCORE_FAMILIES"]["payload"],
        )
        self.assertIn(
            "4_event_response_uncertainty_score_<horizon>",
            rows["EVENT_FAILURE_RISK_VECTOR_SCORE_FAMILIES"]["payload"],
        )
        self.assertEqual(rows["ALPHA_CONFIDENCE_VECTOR_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("5_alpha_direction_score_<horizon>", rows["ALPHA_CONFIDENCE_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("5_alpha_tradability_score_<horizon>", rows["ALPHA_CONFIDENCE_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("5_base_alpha_direction_score_<horizon>", rows["ALPHA_CONFIDENCE_BASE_DIAGNOSTIC_SCORE_FAMILIES"]["payload"])
        self.assertIn(
            "5_market_adjusted_alpha_score_<horizon>",
            rows["ALPHA_CONFIDENCE_BASELINE_ADJUSTMENT_DIAGNOSTIC_SCORE_FAMILIES"]["payload"],
        )
        self.assertIn(
            "5_event_adjustment_reason_codes_<horizon>",
            rows["ALPHA_CONFIDENCE_EVENT_ADJUSTMENT_DIAGNOSTIC_FIELD_FAMILIES"]["payload"],
        )
        self.assertEqual(
            rows["ALPHA_CONFIDENCE_VECTOR_OUTPUT_TIER_POLICY"]["payload"],
            "base_unadjusted_diagnostic_only;final_adjusted_layer_5_facing",
        )
        self.assertEqual(rows["POSITION_PROJECTION_MODEL"]["payload"], "position_projection_model")
        self.assertEqual(rows["MODEL_07_POSITION_PROJECTION"]["payload"], "model_07_position_projection")
        self.assertEqual(rows["POSITION_PROJECTION_VECTOR"]["payload"], "position_projection_vector")
        self.assertEqual(rows["POSITION_PROJECTION_VECTOR_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("7_target_exposure_score_<horizon>", rows["POSITION_PROJECTION_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("7_projection_confidence_score_<horizon>", rows["POSITION_PROJECTION_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("7_resolved_target_exposure_score", rows["POSITION_PROJECTION_HANDOFF_SUMMARY_FIELD_FAMILIES"]["payload"])
        self.assertIn("7_effective_current_exposure_score", rows["POSITION_PROJECTION_DIAGNOSTIC_FIELD_FAMILIES"]["payload"])
        self.assertIn("target_exposure_not_order_quantity", rows["POSITION_PROJECTION_BOUNDARY_POLICY"]["payload"])
        self.assertEqual(rows["CURRENT_POSITION_STATE"]["payload"], "current_position_state")
        self.assertEqual(rows["PENDING_POSITION_STATE"]["payload"], "pending_position_state")
        self.assertEqual(rows["EFFECTIVE_CURRENT_EXPOSURE"]["payload"], "effective_current_exposure")
        self.assertEqual(rows["UNDERLYING_ACTION_MODEL"]["payload"], "underlying_action_model")
        self.assertEqual(rows["MODEL_08_UNDERLYING_ACTION"]["payload"], "model_08_underlying_action")
        self.assertEqual(rows["UNDERLYING_ACTION_PLAN"]["payload"], "underlying_action_plan")
        self.assertEqual(rows["UNDERLYING_ACTION_VECTOR"]["payload"], "underlying_action_vector")
        self.assertEqual(rows["UNDERLYING_ACTION_VECTOR_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn(
            "8_underlying_trade_eligibility_score_<horizon>",
            rows["UNDERLYING_ACTION_VECTOR_SCORE_FAMILIES"]["payload"],
        )
        self.assertIn(
            "8_underlying_action_confidence_score_<horizon>",
            rows["UNDERLYING_ACTION_VECTOR_SCORE_FAMILIES"]["payload"],
        )
        self.assertIn("8_resolved_underlying_action_type", rows["UNDERLYING_ACTION_RESOLVED_FIELD_FAMILIES"]["payload"])
        self.assertIn("open_long", rows["UNDERLYING_ACTION_PLANNED_ACTION_TYPES"]["payload"])
        self.assertIn("bearish_underlying_path_but_no_short_allowed", rows["UNDERLYING_ACTION_PLANNED_ACTION_TYPES"]["payload"])
        self.assertIn("planned_quantity_not_final_order_quantity", rows["UNDERLYING_ACTION_BOUNDARY_POLICY"]["payload"])
        self.assertEqual(rows["CURRENT_UNDERLYING_POSITION_STATE"]["payload"], "current_underlying_position_state")
        self.assertEqual(rows["PENDING_UNDERLYING_ORDER_STATE"]["payload"], "pending_underlying_order_state")
        self.assertEqual(rows["EFFECTIVE_CURRENT_UNDERLYING_EXPOSURE"]["payload"], "effective_current_underlying_exposure")
        self.assertEqual(rows["BACKGROUND_CONTEXT_MODEL"]["payload"], "background_context_model")
        self.assertEqual(rows["MODEL_01_BACKGROUND_CONTEXT"]["payload"], "model_01_background_context")
        self.assertEqual(rows["BACKGROUND_CONTEXT_STATE"]["payload"], "background_context_state")
        self.assertEqual(rows["BACKGROUND_CONTEXT_STATE_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("1_market_direction_score_<horizon>", rows["BACKGROUND_CONTEXT_STATE_SCORE_FAMILIES"]["payload"])
        self.assertIn("1_background_context_quality_score_<horizon>", rows["BACKGROUND_CONTEXT_STATE_SCORE_FAMILIES"]["payload"])
        self.assertEqual(rows["TARGET_STATE_MODEL"]["payload"], "target_state_model")
        self.assertEqual(rows["MODEL_02_TARGET_STATE"]["payload"], "model_02_target_state")
        self.assertEqual(rows["TARGET_CONTEXT_STATE"]["payload"], "target_context_state")
        self.assertEqual(rows["TARGET_CONTEXT_STATE_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("2_target_direction_score_<horizon>", rows["TARGET_CONTEXT_STATE_SCORE_FAMILIES"]["payload"])
        self.assertIn("2_tradability_score_<horizon>", rows["TARGET_CONTEXT_STATE_SCORE_FAMILIES"]["payload"])
        self.assertEqual(rows["EVENT_STATE_MODEL"]["payload"], "event_state_model")
        self.assertEqual(rows["MODEL_03_EVENT_STATE"]["payload"], "model_03_event_state")
        self.assertEqual(rows["EVENT_STATE_VECTOR"]["payload"], "event_state_vector")
        self.assertEqual(rows["EVENT_STATE_VECTOR_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("3_event_response_direction_score_<horizon>", rows["EVENT_STATE_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("3_event_applicability_confidence_score_<horizon>", rows["EVENT_STATE_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("3_event_option_price_impact_score_<horizon>", rows["EVENT_STATE_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("3_event_expiry_gamma_flow_impact_score_<horizon>", rows["EVENT_STATE_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("option_liquidity_spread", rows["EVENT_STATE_VECTOR_IMPACT_CHANNELS"]["payload"])
        self.assertEqual(rows["UNIFIED_DECISION_MODEL"]["payload"], "unified_decision_model")
        self.assertEqual(rows["MODEL_04_UNIFIED_DECISION"]["payload"], "model_04_unified_decision")
        self.assertEqual(rows["UNIFIED_DECISION_VECTOR"]["payload"], "unified_decision_vector")
        self.assertEqual(rows["UNIFIED_DECISION_VECTOR_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("4_edge_direction_score_<horizon>", rows["UNIFIED_DECISION_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("4_action_confidence_score_<horizon>", rows["UNIFIED_DECISION_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("4_resolved_underlying_action_type", rows["UNIFIED_DECISION_RESOLVED_FIELD_FAMILIES"]["payload"])
        self.assertIn("4_resolved_reason_codes", rows["UNIFIED_DECISION_RESOLVED_FIELD_FAMILIES"]["payload"])
        self.assertIn("open_long", rows["UNIFIED_DECISION_PLANNED_ACTION_TYPES"]["payload"])
        self.assertIn("bearish_underlying_path_but_no_short_allowed", rows["UNIFIED_DECISION_PLANNED_ACTION_TYPES"]["payload"])
        self.assertIn("limit_near_mid", rows["UNIFIED_DECISION_ENTRY_STYLES"]["payload"])
        self.assertIn("no_entry", rows["UNIFIED_DECISION_ENTRY_STYLES"]["payload"])
        self.assertEqual(rows["OPTION_EXPRESSION_MODEL"]["payload"], "option_expression_model")
        self.assertEqual(rows["MODEL_05_OPTION_EXPRESSION"]["payload"], "model_05_option_expression")
        self.assertEqual(rows["OPTION_EXPRESSION_PLAN"]["payload"], "option_expression_plan")
        self.assertEqual(rows["EXPRESSION_VECTOR"]["payload"], "expression_vector")
        self.assertEqual(rows["OPTION_EXPRESSION_VECTOR_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("M05_after_unified_decision", rows["OPTION_EXPRESSION_MODEL_LAYER_POLICY"]["payload"])
        self.assertIn("5_option_expression_eligibility_score_<horizon>", rows["OPTION_EXPRESSION_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("5_option_theta_risk_score_<horizon>", rows["OPTION_EXPRESSION_VECTOR_SCORE_FAMILIES"]["payload"])
        self.assertIn("5_resolved_expression_type", rows["OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES"]["payload"])
        self.assertIn("5_resolved_selected_contract_ref", rows["OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES"]["payload"])
        self.assertIn("5_resolved_no_option_reason_codes", rows["OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES"]["payload"])
        self.assertIn("long_call", rows["OPTION_EXPRESSION_TYPES"]["payload"])
        self.assertIn("underlying_only_expression", rows["OPTION_EXPRESSION_TYPES"]["payload"])
        self.assertIn("option_expression_not_broker_order", rows["OPTION_EXPRESSION_BOUNDARY_POLICY"]["payload"])
        self.assertIn("underlying_only_expression_allowed_when_options_unsuitable", rows["OPTION_EXPRESSION_BOUNDARY_POLICY"]["payload"])
        self.assertIn("maintain_or_no_trade_means_no_option_expression", rows["OPTION_EXPRESSION_BOUNDARY_POLICY"]["payload"])
        self.assertIn("preferred_delta_range_hard_filter", rows["OPTION_EXPRESSION_BOUNDARY_POLICY"]["payload"])
        self.assertIn("target_range_moneyness_guardrail", rows["OPTION_EXPRESSION_BOUNDARY_POLICY"]["payload"])
        self.assertIn("5_candidate_hard_filter_fail_reason_codes", rows["OPTION_EXPRESSION_DIAGNOSTIC_FIELD_FAMILIES"]["payload"])
        self.assertIn("bullish_call_strike_not_above_target_price_high", rows["OPTION_EXPRESSION_MONEYNESS_GUARDRAIL"]["payload"])
        self.assertEqual(rows["OPTION_CHAIN_SNAPSHOT_REF"]["payload"], "option_chain_snapshot_ref")
        self.assertEqual(rows["UNDERLYING_QUOTE_SNAPSHOT_REF"]["payload"], "underlying_quote_snapshot_ref")
        self.assertEqual(rows["PENDING_OPTION_EXPOSURE_CONTEXT"]["payload"], "pending_option_exposure_context")
        self.assertIn("underlying_only_expression", rows["OPTION_EXPRESSION_BASELINE_LADDER"]["payload"])
        self.assertIn("underlying_target_hit_but_option_lost_label_<horizon>", rows["OPTION_EXPRESSION_EVALUATION_LABEL_FAMILIES"]["payload"])
        self.assertEqual(rows["RESIDUAL_EVENT_GOVERNANCE_MODEL"]["payload"], "residual_event_governance_model")
        self.assertEqual(rows["MODEL_06_RESIDUAL_EVENT_GOVERNANCE"]["payload"], "model_06_residual_event_governance")
        self.assertEqual(rows["RESIDUAL_EVENT_GOVERNANCE_VECTOR_HORIZONS"]["payload"], "model_decision_horizon_grid")
        self.assertIn("6_event_presence_score_<horizon>", rows["RESIDUAL_EVENT_GOVERNANCE_CORE_SCORE_FAMILIES"]["payload"])
        self.assertIn("6_event_contagion_risk_score_<horizon>", rows["RESIDUAL_EVENT_GOVERNANCE_CORE_SCORE_FAMILIES"]["payload"])
        self.assertIn("6_event_market_impact_score_<horizon>", rows["RESIDUAL_EVENT_GOVERNANCE_IMPACT_SCORE_FAMILIES"]["payload"])
        self.assertIn("6_event_target_relevance_score_<horizon>", rows["RESIDUAL_EVENT_GOVERNANCE_IMPACT_SCORE_FAMILIES"]["payload"])
        self.assertIn("6_event_option_impact_score_<horizon>", rows["RESIDUAL_EVENT_GOVERNANCE_IMPACT_SCORE_FAMILIES"]["payload"])
        self.assertIn("earnings_iv_crush", rows["RESIDUAL_EVENT_GOVERNANCE_OPTION_SENSITIVE_EVENT_FAMILIES"]["payload"])
        self.assertIn("volatility_surface", rows["RESIDUAL_EVENT_GOVERNANCE_IMPACT_CHANNELS"]["payload"])
        self.assertIn("6_resolved_intervention_action", rows["RESIDUAL_EVENT_GOVERNANCE_RESOLVED_FIELD_FAMILIES"]["payload"])
        self.assertIn("6_resolved_reason_codes", rows["RESIDUAL_EVENT_GOVERNANCE_RESOLVED_FIELD_FAMILIES"]["payload"])
        self.assertIn("block_new_entry", rows["RESIDUAL_EVENT_GOVERNANCE_INTERVENTION_ACTIONS"]["payload"])
        self.assertIn("reduce_or_flatten_review", rows["RESIDUAL_EVENT_GOVERNANCE_INTERVENTION_ACTIONS"]["payload"])
        self.assertIn("dataset_snapshot_ref", rows["MODEL_PROMOTION_READINESS_CHECKLIST"]["payload"])
        self.assertIn("calibration_report_ref", rows["MODEL_PROMOTION_READINESS_CHECKLIST"]["payload"])
        self.assertIn("layer_2_deferred", rows["MODEL_PROMOTION_READINESS_STATUS_MATRIX"]["payload"])
        self.assertEqual(rows["MODEL_PROMOTION_REVIEW"]["payload"], "model_promotion_review")
        self.assertIn("every model layer", rows["MODEL_PROMOTION_REVIEW"]["note"])
        self.assertIn("manager_schedules_only", rows["MODEL_PROMOTION_UNIFIED_REVIEW_POLICY"]["payload"])
        self.assertIn("evaluation_owns_replay_settlement_eligibility_readiness", rows["MODEL_PROMOTION_UNIFIED_REVIEW_POLICY"]["payload"])
        self.assertIn("execution_owns_shadow_cycle_activation", rows["MODEL_PROMOTION_UNIFIED_REVIEW_POLICY"]["payload"])
        self.assertEqual(
            rows["MODEL_PROMOTION_UNIFIED_TARGETS"]["payload"],
            "background_context_model;target_state_model;event_state_model;unified_decision_model;option_expression_model;residual_event_governance_model",
        )
        self.assertIn("Canonical stable model ids", rows["MODEL_PROMOTION_UNIFIED_TARGETS"]["note"])
        self.assertEqual(rows["MANAGER_MODEL_PROMOTION_REVIEW_PLAN"]["kind"], "script")
        self.assertEqual(rows["MANAGER_TASK_SYSTEM_REHEARSAL"]["kind"], "script")
        self.assertEqual(rows["MANAGER_TASK_SYSTEM_REHEARSAL"]["payload"], "PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py")
        self.assertEqual(rows["MANAGER_TASK_SYSTEM_REHEARSAL_ARTIFACT"]["kind"], "artifact_type")
        self.assertIn("ready_signal", rows["MANAGER_TASK_SYSTEM_REHEARSAL_ARTIFACT"]["applies_to"])
        self.assertNotIn("MODEL_01_PROMOTION_REVIEW", rows)
        self.assertNotIn("MODEL_09_PROMOTION_REVIEW", rows)
        self.assertEqual(rows["TRADE_RISK_CAP"]["payload"], "trade_risk_cap")
        self.assertIn("max_loss_usd", rows["TRADE_RISK_CAP_REQUIRED_FIELDS"]["payload"])
        self.assertIn("long_option_premium_defined_risk", rows["TRADE_RISK_CAP_ENFORCEMENT_MODES"]["payload"])
        self.assertIn("warn_only_not_allowed", rows["TRADE_RISK_CAP_FAILURE_POLICY"]["payload"])
        self.assertIn("layer_1_deferred_after_real_evaluation", rows["MODEL_PROMOTION_READINESS_STATUS_MATRIX"]["payload"])
        self.assertIn("layer_3_real_production_eval_substrate_deferred_upstream_dependencies_and_calibration", rows["MODEL_PROMOTION_READINESS_STATUS_MATRIX"]["payload"])
        self.assertIn("layer_8_agent_reviewed_deferred_no_production_eval_substrate", rows["MODEL_PROMOTION_READINESS_STATUS_MATRIX"]["payload"])
        self.assertIn("M01:background_context_model:no_persisted_decision_receipt", rows["MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS"]["payload"])
        self.assertIn("M06:residual_event_governance_model:no_persisted_decision_receipt", rows["MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS"]["payload"])
        self.assertEqual(rows["CURRENT_MODEL_CHAIN_RECEIPT"]["payload"], "current_model_chain_receipt")
        self.assertIn("activation_allowed=false", rows["CURRENT_MODEL_CHAIN_RECEIPT"]["note"])
        self.assertEqual(
            rows["CURRENT_MODEL_CHAIN_MODEL_ORDER"]["payload"],
            "model_01_background_context;model_02_target_state;model_03_event_state;model_04_unified_decision;model_05_option_expression;model_06_residual_event_governance",
        )
        self.assertIn("underlying_action_plan_ref", rows["CURRENT_MODEL_CHAIN_RETIRED_FIELD_GUARD"]["payload"])
        self.assertIn("event_context_vector_ref", rows["CURRENT_MODEL_CHAIN_RETIRED_FIELD_GUARD"]["payload"])
        self.assertEqual(rows["REVIEW_LAYERS_03_10_PROMOTION_ACCEPTANCE"]["kind"], "script")
        self.assertIn("review_layers_03_10_promotion_acceptance.py", rows["REVIEW_LAYERS_03_10_PROMOTION_ACCEPTANCE"]["path"])
        self.assertEqual(rows["REVIEW_LAYER_03_TARGET_STATE_VECTOR_PRODUCTION_SUBSTRATE"]["kind"], "script")
        self.assertIn("review_target_state_vector_production_substrate.py", rows["REVIEW_LAYER_03_TARGET_STATE_VECTOR_PRODUCTION_SUBSTRATE"]["path"])
        expected_layer_script_paths = {
            "CURRENT_MODEL_CHAIN_RUN": "scripts/models/run_current_model_chain.py",
            "MODEL_10_EVENT_RISK_GOVERNOR_GENERATE": "scripts/models/model_10_event_risk_governor/generate_model_10_event_risk_governor.py",
            "MODEL_10_EVENT_RISK_GOVERNOR_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_10_event_risk_governor/evaluate_model_10_event_risk_governor.py",
            "MODEL_10_EVENT_RISK_GOVERNOR_REVIEW_PROMOTION": "scripts/models/model_10_event_risk_governor/review_event_risk_governor_promotion.py",
            "MODEL_05_ALPHA_CONFIDENCE_GENERATE": "scripts/models/model_05_alpha_confidence/generate_model_05_alpha_confidence.py",
            "MODEL_05_ALPHA_CONFIDENCE_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_05_alpha_confidence/evaluate_model_05_alpha_confidence.py",
            "MODEL_01_MARKET_REGIME_DIAGNOSE_SUBSTRATE": "scripts/models/model_01_market_regime/diagnose_model_01_market_regime_substrate.py",
            "MODEL_05_ALPHA_CONFIDENCE_REVIEW_PROMOTION": "scripts/models/model_05_alpha_confidence/review_alpha_confidence_promotion.py",
            "MODEL_01_BACKGROUND_CONTEXT_GENERATE": "scripts/models/model_01_background_context/generate_model_01_background_context.py",
            "MODEL_01_BACKGROUND_CONTEXT_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_01_background_context/evaluate_model_01_background_context.py",
            "MODEL_01_BACKGROUND_CONTEXT_REVIEW_PROMOTION": "scripts/models/model_01_background_context/review_background_context_promotion.py",
            "MODEL_02_TARGET_STATE_GENERATE": "scripts/models/model_02_target_state/generate_model_02_target_state.py",
            "MODEL_02_TARGET_STATE_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_02_target_state/evaluate_model_02_target_state.py",
            "MODEL_02_TARGET_STATE_REVIEW_PROMOTION": "scripts/models/model_02_target_state/review_target_state_promotion.py",
            "MODEL_03_EVENT_STATE_GENERATE": "scripts/models/model_03_event_state/generate_model_03_event_state.py",
            "MODEL_03_EVENT_STATE_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_03_event_state/evaluate_model_03_event_state.py",
            "MODEL_03_EVENT_STATE_REVIEW_PROMOTION": "scripts/models/model_03_event_state/review_event_state_promotion.py",
            "MODEL_04_UNIFIED_DECISION_GENERATE": "scripts/models/model_04_unified_decision/generate_model_04_unified_decision.py",
            "MODEL_04_UNIFIED_DECISION_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_04_unified_decision/evaluate_model_04_unified_decision.py",
            "MODEL_04_UNIFIED_DECISION_REVIEW_PROMOTION": "scripts/models/model_04_unified_decision/review_unified_decision_promotion.py",
            "MODEL_05_OPTION_EXPRESSION_GENERATE": "scripts/models/model_05_option_expression/generate_model_05_option_expression.py",
            "MODEL_05_OPTION_EXPRESSION_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_05_option_expression/evaluate_model_05_option_expression.py",
            "MODEL_05_OPTION_EXPRESSION_REVIEW_PROMOTION": "scripts/models/model_05_option_expression/review_option_expression_promotion.py",
            "MODEL_06_RESIDUAL_EVENT_GOVERNANCE_GENERATE": "scripts/models/model_06_residual_event_governance/generate_model_06_residual_event_governance.py",
            "MODEL_06_RESIDUAL_EVENT_GOVERNANCE_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_06_residual_event_governance/evaluate_model_06_residual_event_governance.py",
            "MODEL_06_RESIDUAL_EVENT_GOVERNANCE_REVIEW_PROMOTION": "scripts/models/model_06_residual_event_governance/review_residual_event_governance_promotion.py",
            "MODEL_07_POSITION_PROJECTION_GENERATE": "scripts/models/model_07_position_projection/generate_model_07_position_projection.py",
            "MODEL_07_POSITION_PROJECTION_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_07_position_projection/evaluate_model_07_position_projection.py",
            "MODEL_07_POSITION_PROJECTION_REVIEW_PROMOTION": "scripts/models/model_07_position_projection/review_position_projection_promotion.py",
            "MODEL_08_UNDERLYING_ACTION_GENERATE": "scripts/models/model_08_underlying_action/generate_model_08_underlying_action.py",
            "MODEL_08_UNDERLYING_ACTION_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_08_underlying_action/evaluate_model_08_underlying_action.py",
            "MODEL_08_UNDERLYING_ACTION_REVIEW_PROMOTION": "scripts/models/model_08_underlying_action/review_underlying_action_promotion.py",
            "MODEL_09_OPTION_EXPRESSION_GENERATE": "scripts/models/model_09_option_expression/generate_model_09_option_expression.py",
            "MODEL_09_OPTION_EXPRESSION_EVALUATE_PROMOTION_EVIDENCE": "scripts/models/model_09_option_expression/evaluate_model_09_option_expression.py",
            "MODEL_09_OPTION_EXPRESSION_REVIEW_PROMOTION": "scripts/models/model_09_option_expression/review_option_expression_promotion.py",
            "M01_MARKET_REGIME_FEATURE_GENERATION_GENERATE": "src/data_feature/m01_market_regime_feature_generation/__main__.py",
            "M02_SECTOR_CONTEXT_FEATURE_GENERATION_GENERATE": "src/data_feature/m02_sector_context_feature_generation/__main__.py",
            "M03_TARGET_STATE_VECTOR_FEATURE_GENERATION_GENERATE": "src/data_feature/m03_target_state_vector_feature_generation/__main__.py",
            "OPTION_CHAIN_STATE_SOURCE_RUN": "src/data_source/option_chain_state_source/__main__.py",
            "M10_EVENT_RISK_GOVERNOR_FEATURE_GENERATION_GENERATE": "src/data_feature/m10_event_risk_governor_feature_generation/__main__.py",
            "M09_OPTION_EXPRESSION_FEATURE_GENERATION_GENERATE": "src/data_feature/m09_option_expression_feature_generation/__main__.py",
        }
        for key, expected_path in expected_layer_script_paths.items():
            self.assertEqual(rows[key]["kind"], "script")
            self.assertEqual(rows[key]["payload_format"], "command")
            self.assertIn(expected_path, rows[key]["path"])
        self.assertIn("--table-scope current", rows["MODEL_OUTPUT_TABLE_QUALITY_AUDIT"]["payload"])
        self.assertIn("trading_model.model_06_residual_event_governance", rows["MODEL_OUTPUT_TABLE_QUALITY_AUDIT"]["applies_to"])
        self.assertNotIn("trading_model.model_10_event_risk_governor", rows["MODEL_OUTPUT_TABLE_QUALITY_AUDIT"]["applies_to"])
        self.assertIn("current six-model output table families", rows["MODEL_OUTPUT_QUALITY_GATE"]["note"])
        self.assertIn("option_expression_model", rows["M09_OPTION_EXPRESSION_DATA_ACQUISITION_CONTRACT_PATH"]["applies_to"])
        self.assertNotIn("position_execution_model", rows["M09_OPTION_EXPRESSION_DATA_ACQUISITION_CONTRACT_PATH"]["applies_to"])
        self.assertIn("retired_ordinary_candidate_route", rows["M02_SECTOR_CONTEXT_DATA_ACQUISITION"]["applies_to"])
        self.assertNotIn("anonymous_target_candidate_builder", rows["M02_SECTOR_CONTEXT_DATA_ACQUISITION"]["applies_to"])
        self.assertNotIn("model_03_target_state_vector", rows["M02_SECTOR_CONTEXT_DATA_ACQUISITION"]["applies_to"])
        self.assertNotIn("sector_context_model", rows["M02_SECTOR_CONTEXT_DATA_ACQUISITION"]["applies_to"])
        self.assertIn("layer_3_real_eval_deferred_upstream_layer_1_2_not_active_and_calibration_missing", rows["MODEL_PROMOTION_ACCEPTANCE_BLOCKERS"]["payload"])
        self.assertIn("layers_4_10_missing_production_eval_run_labels_metrics", rows["MODEL_PROMOTION_ACCEPTANCE_BLOCKERS"]["payload"])
        self.assertIn("layer_6_dynamic_risk_policy_physical_implementation_pending", rows["MODEL_PROMOTION_ACCEPTANCE_BLOCKERS"]["payload"])
        self.assertIn("data_source_model_input_design_closed", rows["TRADING_DATA_STACK_ACCEPTANCE_STATUS"]["payload"])
        self.assertIn("default_next_regular_us_session_open_after_as_of_date", rows["ETF_HOLDINGS_AVAILABLE_TIME_POLICY"]["payload"])
        self.assertEqual(rows["EQUITY_ABNORMAL_ACTIVITY_MODEL_STANDARD"]["payload"], "equity_abnormal_activity_conservative")
        self.assertEqual(
            rows["ABNORMAL_ACTIVITY_EVIDENCE_FAMILY_SET"]["payload"],
            "price_action_pattern;residual_market_structure_disturbance;microstructure_liquidity_disruption;option_derivatives_abnormality",
        )
        self.assertEqual(
            rows["EVENT_ABNORMAL_ACTIVITY_EVIDENCE_CATEGORIES"]["payload"],
            "abnormal_activity_evidence_family_set",
        )
        self.assertEqual(
            rows["ABNORMALITY_COVERAGE_COMPLETE_REQUIRED_FAMILIES"]["payload"],
            "abnormal_activity_evidence_family_set",
        )
        self.assertEqual(
            rows["ACTIVITY_PRICE_RELATIONSHIP_PROOF_GATE_REQUIREMENT"]["payload"],
            "required_before_event_activity_bridge_model_promotion",
        )
        self.assertEqual(
            rows["ACTIVITY_PRICE_RELATIONSHIP_PROOF_GATE"]["payload"],
            "activity_price_relationship_proof_gate_requirement",
        )
        self.assertEqual(
            rows["ACTIVITY_PRICE_CROSS_SECTION_STUDY_REQUIRED"]["payload"],
            "activity_price_relationship_proof_gate_requirement",
        )
        self.assertIn("historical_calibration_required", rows["EQUITY_ABNORMAL_ACTIVITY_CALIBRATION_STATUS"]["payload"])
        self.assertIn("manager_request", rows["MANAGER_STORAGE_HANDOFF_CONTRACTS"]["payload"])
        self.assertIn("run_manifest", rows["MANAGER_STORAGE_HANDOFF_CONTRACTS"]["payload"])
        self.assertIn("artifact_ref", rows["MANAGER_STORAGE_HANDOFF_CONTRACTS"]["payload"])
        self.assertIn("ready_signal", rows["MANAGER_STORAGE_HANDOFF_CONTRACTS"]["payload"])
        self.assertIn("promoted_model_bodies_keep_forever", rows["STORAGE_LIFECYCLE_POLICY"]["payload"])
        self.assertIn("quarantined_for_delete", rows["STORAGE_LIFECYCLE_STATE_VALUES"]["payload"])
        self.assertIn("direct_readable", rows["STORAGE_READ_MODE_VALUES"]["payload"])
        self.assertIn("provider_window_limited", rows["STORAGE_REPRODUCIBILITY_CLASS_VALUES"]["payload"])
        self.assertEqual(rows["STORAGE_LIFECYCLE_REQUEST"]["kind"], "request_type")
        self.assertEqual(rows["COMPRESSION_RECEIPT"]["kind"], "manifest_type")
        self.assertEqual(rows["DELETION_RECEIPT"]["payload"], "deletion_receipt")
        self.assertEqual(rows["ARTIFACT_TOMBSTONE"]["kind"], "artifact_type")
        self.assertIn("artifact_index", rows["STORAGE_ARTIFACT_INDEX"]["payload"])
        expected_storage_lifecycle_scripts = {
            "STORAGE_SQL_ARCHIVE_EXECUTE": "scripts/lifecycle/execute_sql_archive.py",
            "STORAGE_SQL_ARCHIVE_RESTORE_VERIFY": "scripts/lifecycle/verify_sql_archive_restore.py",
            "STORAGE_QUARANTINE_DELETE_RESULT_BUILD": "scripts/lifecycle/build_quarantine_delete_result.py",
        }
        for key, expected_path in expected_storage_lifecycle_scripts.items():
            self.assertEqual(rows[key]["kind"], "script")
            self.assertEqual(rows[key]["payload_format"], "command")
            self.assertIn(expected_path, rows[key]["path"])
            self.assertIn("trading-storage", rows[key]["applies_to"])
            self.assertIn("no ", rows[key]["note"].lower())
        self.assertIn("--apply-reviewed-archive", rows["STORAGE_SQL_ARCHIVE_EXECUTE"]["note"])
        self.assertIn("verification-only", rows["STORAGE_SQL_ARCHIVE_RESTORE_VERIFY"]["note"])
        self.assertIn("planned_not_executed", rows["STORAGE_QUARANTINE_DELETE_RESULT_BUILD"]["note"])
        self.assertIn("manager_unified_request_task_summary_surface", rows["STORAGE_LIFECYCLE_MANAGER_CONTROL_POLICY"]["payload"])
        self.assertIn("trading_storage_protected_set_physical_execution", rows["STORAGE_LIFECYCLE_MANAGER_CONTROL_POLICY"]["payload"])
        self.assertIn("promotion_classifies_artifacts", rows["PROMOTION_STORAGE_LIFECYCLE_BOUNDARY_POLICY"]["payload"])
        self.assertIn("manager_schedules_lifecycle", rows["PROMOTION_STORAGE_LIFECYCLE_BOUNDARY_POLICY"]["payload"])
        self.assertIn("near_to_far_listed_expirations", rows["LAYER_09_OPTION_BUCKET_EXPIRATION_POLICY"]["payload"])
        self.assertIn("three_listed_strike_levels_below", rows["LAYER_09_OPTION_BUCKET_STRIKE_POLICY"]["payload"])
        self.assertIn("thetadata_strike_range_5_closed_loop_default", rows["LAYER_09_OPTION_BUCKET_STRIKE_POLICY"]["payload"])
        self.assertIn("no_acquisition_time_prefilter_for_model_construction", rows["LAYER_09_OPTION_BUCKET_PREFILTER_POLICY"]["payload"])
        self.assertIn("single_leg_only", rows["LAYER_09_OPTION_EXPRESSION_SINGLE_LEG_POLICY"]["payload"])
        self.assertIn("underlying_only_expression_non_option_fallback", rows["LAYER_09_OPTION_EXPRESSION_SINGLE_LEG_POLICY"]["payload"])
        self.assertNotIn("live_" + "calls_disabled_by_default", rows["DATA_PRODUCTION_HARDENING_POLICY"]["payload"])
        self.assertEqual(rows["MANAGER_CONTROLLED_INFORMATION_PASS"]["payload"], "manager_controlled_information_pass")
        self.assertIn("plan_controlled_information_pass.py", rows["MANAGER_CONTROLLED_INFORMATION_PASS_PLAN"]["path"])
        self.assertIn("provider_calls_zero", rows["MANAGER_CONTROLLED_INFORMATION_PASS_POLICY"]["payload"])
        self.assertIn("checkpoint_resume_required_for_segmented_runs", rows["DATA_PRODUCTION_HARDENING_POLICY"]["payload"])
        self.assertIn("provider_allowlist_required", rows["PROVIDER_CALL_GUARDRAILS_POLICY"]["payload"])
        self.assertIn("segment_id_required", rows["CHECKPOINT_RESUME_POLICY"]["payload"])
        self.assertEqual(rows["RUN_MANIFEST"]["kind"], "manifest_type")
        self.assertEqual(rows["RUN_MANIFEST"]["payload"], "run_manifest")
        self.assertEqual(rows["DATA_SOURCE_RUN_REQUEST"]["kind"], "request_type")
        self.assertEqual(rows["DATA_SOURCE_RUN_REQUEST"]["payload"], "data_source_run")
        self.assertEqual(rows["MODEL_EVAL_READY_SIGNAL"]["kind"], "ready_signal_type")
        self.assertEqual(rows["MODEL_EVAL_READY_SIGNAL"]["payload"], "model_eval_ready")
        self.assertEqual(rows["MODEL_PROMOTION_EVIDENCE_ARTIFACT"]["kind"], "artifact_type")
        self.assertEqual(rows["MODEL_PROMOTION_EVIDENCE_ARTIFACT"]["payload"], "model_promotion_evidence")
        self.assertNotIn("TRADING_PROJECTION_MODEL", rows)
        self.assertNotIn("MODEL_07_TRADING_PROJECTION", rows)
        self.assertNotIn("TRADING_SIGNAL_VECTOR", rows)
        self.assertEqual(rows["MARKET_DIRECTION_SCORE"]["payload"], "1_market_direction_score")
        self.assertEqual(rows["MARKET_TREND_QUALITY_SCORE"]["payload"], "1_market_trend_quality_score")
        self.assertEqual(rows["MARKET_LIQUIDITY_SUPPORT_SCORE"]["payload"], "1_market_liquidity_support_score")
        self.assertNotIn("MARKET_COVERAGE_SCORE", rows)
        self.assertNotIn("MARKET_DATA_QUALITY_SCORE", rows)
        for retired_layer_one_field in {
            "PRICE_BEHAVIOR_FACTOR",
            "TREND_CERTAINTY_FACTOR",
            "CAPITAL_FLOW_FACTOR",
            "SENTIMENT_FACTOR",
            "VALUATION_PRESSURE_FACTOR",
            "FUNDAMENTAL_STRENGTH_FACTOR",
            "MACRO_ENVIRONMENT_FACTOR",
            "MARKET_STRUCTURE_FACTOR",
            "RISK_STRESS_FACTOR",
            "TRANSITION_PRESSURE",
            "DATA_QUALITY_SCORE",
        }:
            self.assertNotIn(retired_layer_one_field, rows)
        self.assertNotIn("TARGET_STATE_VECTOR_TRAILING_STATE_WINDOWS", rows)
        self.assertNotIn("04_TRADE_QUALITY_MODEL_INPUTS", rows)
        self.assertNotIn("04_TRADE_QUALITY_MODEL_INPUTS_BUNDLE_CONFIG", rows)
        self.assertNotIn("06_EVENT_RISK_GOVERNOR_INPUTS", rows)
        self.assertNotIn("06_EVENT_RISK_GOVERNOR_INPUTS_BUNDLE_CONFIG", rows)
        self.assertNotIn("07_PORTFOLIO_RISK_MODEL_INPUTS", rows)
        self.assertNotIn("07_PORTFOLIO_RISK_MODEL_INPUTS_BUNDLE_CONFIG", rows)

    def test_manager_control_plane_contracts_are_registered_concisely(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        contract_payload = rows["MANAGER_STORAGE_HANDOFF_CONTRACTS"]["payload"]
        for contract_name in {
            "component_ref",
            "manager_request",
            "input_binding",
            "run_manifest",
            "run_step",
            "artifact_ref",
            "ready_signal",
        }:
            self.assertIn(contract_name, contract_payload)

        self.assertEqual(
            rows["MANAGER_CONTRACT_SQL_TABLES"]["payload"],
            "trading_manager.manager_request;trading_manager.input_binding;trading_manager.run_manifest;trading_manager.run_step;trading_manager.artifact_ref;trading_manager.ready_signal;trading_manager.task_summary",
        )
        self.assertEqual(rows["MANAGER_GLOBAL_TASK_SUMMARY_VIEW"]["payload"], "trading_manager.task_summary")
        self.assertEqual(rows["MANAGER_TASK_PRIORITY_VALUES"]["payload"], "critical;high;normal;low;backlog")
        self.assertEqual(rows["COMPONENT_OUTPUT_ARTIFACT"]["payload"], "component_output")
        self.assertEqual(rows["MANAGER_REQUEST_PARAMETER_PAYLOAD"]["payload"], "manager_request_parameter_payload")
        self.assertNotEqual(rows["COMPONENT_OUTPUT_ARTIFACT"]["id"], rows["MANAGER_REQUEST_PARAMETER_PAYLOAD"]["id"])
        self.assertIn("materialize_request_payloads.py", rows["MANAGER_REQUEST_PAYLOAD_MATERIALIZE"]["path"])
        self.assertIn("validate_request_handoff.py", rows["MANAGER_REQUEST_HANDOFF_VALIDATE"]["path"])
        self.assertNotIn("LIVE_" + "CALL_APPROVAL", rows)
        self.assertNotIn("LIVE_" + "CALL_APPROVAL_GATE", rows)
        self.assertNotIn("MANAGER_LIVE_" + "CALL_APPROVAL_VALIDATE", rows)
        self.assertIn("dispatch_and_reconcile_provider_stage.py", rows["MANAGER_PROVIDER_ACQUISITION_DISPATCH"]["path"])
        self.assertIn("current_manager_control_plane_phase_closed", rows["TRADING_MANAGER_CONTROL_PLANE_ACCEPTANCE_STATUS"]["payload"])
        self.assertIn("no_broker_execution_enabled", rows["TRADING_MANAGER_CONTROL_PLANE_ACCEPTANCE_STATUS"]["payload"])
        self.assertIn("continuous_safe_work", rows["MANAGER_AUTONOMOUS_SCHEDULER_POLICY"]["payload"])
        self.assertIn("execution_priority_reserved", rows["MANAGER_AUTONOMOUS_SCHEDULER_POLICY"]["payload"])
        self.assertIn("layer_01_02_foundation_catch_up_priority", rows["MANAGER_AUTONOMOUS_SCHEDULER_POLICY"]["payload"])
        self.assertEqual(rows["MANAGER_FOUNDATION_CATCH_UP_PRIORITY"]["payload"], "layer_01_02_foundation_catch_up_priority")
        self.assertEqual(
            rows["LAYER_01_02_HISTORICAL_CATCH_UP_TO_CURRENT_REQUIRED"]["payload"],
            "layer_01_02_historical_catch_up_to_current_required",
        )
        self.assertEqual(
            rows["POST_MODEL_GENERATION_REBUILD_REQUIRED_AFTER_LAYER_01_02_CATCH_UP"]["payload"],
            "post_model_generation_rebuild_required_after_layer_01_02_catch_up",
        )
        self.assertEqual(
            rows["HISTORICAL_SUBSTRATE_REUSE_POLICY"]["payload"],
            "downloaded_cleaned_feature_substrate_reusable_when_contract_valid",
        )
        self.assertEqual(
            rows["POST_MODEL_ARTIFACT_REBUILD_POLICY"]["payload"],
            "model_generation_evaluation_promotion_artifacts_superseded_until_rebuilt",
        )
        self.assertEqual(rows["PROMOTION_STAGE_TYPE"]["payload"], "promotion_review")
        self.assertEqual(
            rows["FOLD_STACK_PROMOTION_GATE_POLICY"]["payload"],
            "pinned_layer_01_09_pre_replay_generation_then_replay_layer_10_attribution_complete",
        )
        self.assertIn("all-or-nothing", rows["FOLD_STACK_PROMOTION_GATE_POLICY"]["note"])
        self.assertIn("post-replay Layer 10 attribution", rows["FOLD_STACK_PROMOTION_GATE_POLICY"]["note"])
        self.assertIn("fold_layers_01_09_model_generation_complete_required", rows["MODEL_PROMOTION_UNIFIED_REVIEW_POLICY"]["payload"])
        self.assertIn("post_replay_layer_10_attribution_complete_required", rows["MODEL_PROMOTION_UNIFIED_REVIEW_POLICY"]["payload"])
        self.assertEqual(
            rows["DYNAMIC_RISK_POLICY_MODEL_LAYER"]["payload"],
            "layer_06_dynamic_risk_policy_model_global_market_driven_premium_risk_budget_state",
        )
        self.assertIn("global market regime", rows["DYNAMIC_RISK_POLICY_MODEL_LAYER"]["note"])
        self.assertEqual(
            rows["MODEL_REPLAY_CANDIDATE_SELECTION_POLICY"]["payload"],
            "target_substrate_does_not_select_replay_targets_components_choose_candidates_or_combinations",
        )
        self.assertIn("components to choose no target", rows["MODEL_REPLAY_CANDIDATE_SELECTION_POLICY"]["note"])
        self.assertEqual(
            rows["LAYER_10_POST_REPLAY_ATTRIBUTION_POLICY"]["payload"],
            "layer_10_starts_after_concentrated_replay_not_before_replay_input_stage",
        )
        self.assertIn("pre-replay data-acquisition", rows["LAYER_10_POST_REPLAY_ATTRIBUTION_POLICY"]["note"])
        self.assertEqual(
            rows["LAYER_4_FOLD_EVENT_OBSERVATION_POLICY"]["payload"],
            "layer_4_global_sector_event_observation_substrate_collected_each_fold",
        )
        self.assertIn("collected for each fold", rows["LAYER_4_FOLD_EVENT_OBSERVATION_POLICY"]["note"])
        self.assertIn(
            "materialize_layer_four_event_observation_inputs.py",
            rows["MANAGER_MATERIALIZE_LAYER_FOUR_EVENT_OBSERVATION_INPUTS"]["payload"],
        )
        self.assertIn("model_training_workflow", rows["MANAGER_MATERIALIZE_LAYER_FOUR_EVENT_OBSERVATION_INPUTS"]["applies_to"])
        self.assertNotIn("MANAGER_MATERIALIZE_LAYER_TEN_EVENT_RISK_INPUTS", rows)
        self.assertNotIn("MANAGER_LAYER_TEN_EVENT_RISK_INPUT_MATERIALIZATION", rows)
        self.assertIn(
            "promotion_waits_for_model_group_evaluation_complete",
            rows["MONTHLY_SUBSTRATE_FOLD_MODEL_STAGE_BOUNDARY"]["payload"],
        )
        self.assertEqual(rows["ROLLING_FOLD_FOUR_ONE_ONE_SPLIT"]["kind"], "config")
        self.assertIn("train_months=4", rows["ROLLING_FOLD_FOUR_ONE_ONE_SPLIT"]["payload"])
        self.assertEqual(
            rows["MONTH_SCOPED_INGEST_ONLY_DURING_FOUNDATION_CATCH_UP"]["payload"],
            "month_scoped_layer_01_02_workflow_exposes_data_acquisition_and_feature_generation_only",
        )
        self.assertIn("live_trading_capacity_reserved", rows["MANAGER_RESOURCE_BUDGET_POLICY"]["payload"])
        self.assertIn("historical_worker_count_capacity_adaptive", rows["MANAGER_RESOURCE_BUDGET_POLICY"]["payload"])
        self.assertIn("pre_promotion_full_training_mode", rows["MANAGER_MARKET_HOURS_HISTORICAL_PAUSE_POLICY"]["payload"])
        self.assertIn("market_hours_historical_training_backoff_disabled_until_execution_runtime_activation", rows["MANAGER_MARKET_HOURS_HISTORICAL_PAUSE_POLICY"]["payload"])
        self.assertIn("runtime_activation_requires_execution_shadow_cycle_selection", rows["MANAGER_MARKET_HOURS_HISTORICAL_PAUSE_POLICY"]["payload"])
        self.assertIn("historical_provider_calls_run_autonomously_under_resource_controls", rows["MANAGER_MARKET_HOURS_HISTORICAL_PAUSE_POLICY"]["payload"])
        self.assertEqual(rows["MANAGER_SCHEDULER_DECISION_LOOP"]["payload"], "manager_scheduler_decision_loop")
        self.assertIn("check approval/resource/market-hour gates", rows["MANAGER_SCHEDULER_DECISION_LOOP"]["note"])
        self.assertIn("run_automation_scheduler.py", rows["MANAGER_AUTOMATION_SCHEDULER_RUN"]["path"])
        self.assertIn("run_automation_scheduler_daemon.py", rows["MANAGER_AUTOMATION_SCHEDULER_DAEMON_RUN"]["path"])
        self.assertIn("plan_model_training_workflow.py", rows["MANAGER_MODEL_TRAINING_WORKFLOW_PLAN"]["path"])
        self.assertIn("advance_model_training_workflow.py", rows["MANAGER_MODEL_TRAINING_WORKFLOW_ADVANCE"]["path"])
        self.assertIn("dispatch_and_reconcile_provider_stage.py", rows["MANAGER_PROVIDER_ACQUISITION_DISPATCH"]["path"])
        self.assertIn("execute_model_training_stage.py", rows["MANAGER_SAFE_OFFLINE_STAGE_EXECUTION"]["path"])
        self.assertIn("plan_dataset_expansion.py", rows["MANAGER_DATASET_EXPANSION_PLANNER"]["path"])
        self.assertIn("manager_selects_next_dataset_role", rows["MANAGER_DATASET_EXPANSION_POLICY"]["payload"])
        self.assertIn("provider_calls_use_autonomous_historical_acquisition", rows["MANAGER_DATASET_EXPANSION_POLICY"]["payload"])
        self.assertIn("historical_training_sampling_universe_may_be_broader", rows["HISTORICAL_SAMPLING_VS_LIVE_ROUTING_POLICY"]["payload"])
        self.assertIn("layer_03_targets_may_include_non_selected_sectors", rows["HISTORICAL_SAMPLING_VS_LIVE_ROUTING_POLICY"]["payload"])
        self.assertEqual(rows["HISTORICAL_TRAINING_SAMPLING_UNIVERSE"]["payload"], "historical_training_sampling_universe")
        self.assertEqual(rows["LIVE_INFERENCE_ROUTING_UNIVERSE"]["payload"], "live_inference_routing_universe")
        self.assertEqual(rows["MANAGER_DATASET_EXPANSION_PLAN"]["payload"], "manager_dataset_expansion_plan")
        self.assertEqual(rows["MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT"]["payload"], "manager_model_training_workflow_plan")
        self.assertEqual(rows["MANAGER_MODEL_TRAINING_WORKFLOW_STATE"]["payload"], "manager_model_training_workflow_state")
        self.assertEqual(rows["MANAGER_PROVIDER_DISPATCH_SUMMARY"]["payload"], "manager_provider_dispatch_summary")
        self.assertEqual(rows["MANAGER_STAGE_EXECUTION_SUMMARY"]["payload"], "manager_stage_execution_summary")
        self.assertEqual(rows["SERVER_ERROR_AGENT_REQUEST"]["payload"], "server_error_agent_request")
        self.assertEqual(rows["AGENT_ERROR_DIAGNOSIS"]["payload"], "agent_error_diagnosis")
        self.assertIn("call_agent_for_error.py", rows["MANAGER_AGENT_ERROR_HANDOFF_CALL"]["path"])
        self.assertIn("no_provider_calls", rows["MANAGER_AGENT_ERROR_SAFETY_BOUNDARY"]["payload"])
        self.assertIn("1504100135200620665", rows["MANAGER_AGENT_ERROR_DISCORD_NOTIFICATION_TARGET"]["payload"])
        self.assertIn("best_effort", rows["MANAGER_AGENT_ERROR_DISCORD_NOTIFICATION_POLICY"]["payload"])
        self.assertEqual(rows["SERVER_ERROR_CATALOG_ENTRY"]["payload"], "server_error_catalog_entry")
        self.assertIn("ERR_000001", rows["MANAGER_AGENT_ERROR_NUMBERING_POLICY"]["payload"])
        self.assertIn("list_agent_errors.py", rows["MANAGER_AGENT_ERROR_CATALOG_LIST"]["path"])
        self.assertEqual(rows["SERVER_ERROR_CATALOG_OCCURRENCE"]["payload"], "server_error_catalog_occurrence")
        self.assertIn("dedup_window_seconds=3600", rows["MANAGER_AGENT_ERROR_DEDUP_POLICY"]["payload"])
        self.assertIn("occurred", rows["MANAGER_AGENT_ERROR_ALERT_TIME_POLICY"]["payload"])
        self.assertIn("run_safe_error_repair.py", rows["MANAGER_SAFE_ERROR_REPAIR_RUNNER"]["path"])
        self.assertEqual(
            rows["MANAGER_SAFE_ERROR_REPAIR_RUNNER"]["payload"],
            "PYTHONPATH=src python3 scripts/tasks/run_safe_error_repair.py",
        )
        self.assertEqual(
            rows["MANAGER_AGENT_ERROR_AGENT_RUNNER"]["payload"],
            "PYTHONPATH=src python3 scripts/tasks/run_agent_error_agent.py",
        )
        self.assertEqual(rows["DASHBOARD_HISTORICAL_TASK_TIMELINE"]["payload"], "historical_task_progress_summary.chart_payload.task_timeline")
        self.assertIn("task_timeline", rows["DASHBOARD_HISTORICAL_TASK_PROGRESS_PAGE"]["applies_to"])
        self.assertIn("layer_04_event_failure_risk", rows["MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT"]["applies_to"])
        self.assertIn("model_09_option_expression", rows["MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT"]["applies_to"])
        self.assertIn("layer_06_dynamic_risk_policy", rows["MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT"]["applies_to"])
        self.assertIn("post_replay_layer_10_attribution", rows["MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT"]["applies_to"])
        self.assertEqual(rows["MANAGER_SCHEDULER_DECISION"]["payload"], "manager_scheduler_decision")
        self.assertEqual(rows["MANAGER_SCHEDULER_DAEMON_STATE"]["payload"], "manager_scheduler_daemon_state")
        self.assertIn("historical_scheduler_state.json", rows["MANAGER_HISTORICAL_SCHEDULER_RUNTIME_FILES"]["payload"])
        self.assertEqual(rows["MANAGER_HISTORICAL_SCHEDULER_SYSTEMD_SERVICE"]["kind"], "systemd_unit")
        self.assertEqual(
            rows["MANAGER_HISTORICAL_SCHEDULER_SYSTEMD_SERVICE"]["payload"],
            "trading-manager-historical-scheduler.service",
        )
        self.assertIn("trading-manager-historical-scheduler.service", rows["MANAGER_HISTORICAL_SCHEDULER_SYSTEMD_SERVICE"]["path"])
        self.assertEqual(rows["REVIEW_DECISION_ARTIFACT"]["payload"], "review_decision")
        self.assertNotIn("ACTIVATION_RECORD_ARTIFACT", rows)
        self.assertEqual(rows["EXECUTION_SHADOW_CYCLE_SELECTION"]["payload"], "execution_shadow_cycle_selection")
        self.assertIn("trading-execution", rows["EXECUTION_SHADOW_CYCLE_SELECTION"]["path"])
        self.assertIn("build_review_decision.py", rows["MANAGER_REVIEW_DECISION_BUILD"]["path"])
        self.assertEqual(rows["COMPONENT_COMPLETION_RECEIPT_PAYLOAD"]["payload"], "component_completion_receipt_payload")
        self.assertIn("store_completion_receipt_payload.py", rows["STORAGE_COMPLETION_RECEIPT_PAYLOAD_STORE"]["path"])
        self.assertIn("validate_trade_risk_cap.py", rows["TRADE_RISK_CAP_VALIDATE"]["path"])
        self.assertIn("contract_type;binding_id;input_role", rows["INPUT_BINDING_REQUIRED_FIELDS"]["payload"])
        self.assertIn("contract_type;step_id;run_id", rows["RUN_STEP_REQUIRED_FIELDS"]["payload"])
        self.assertIn("requested", {row["payload"] for row in rows.values() if row["kind"] == "status_value"})
        self.assertIn("deleted", {row["payload"] for row in rows.values() if row["kind"] == "status_value"})

    def test_event_database_scope_is_not_active(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            offenders = [
                (row["key"], row["applies_to"])
                for row in csv.DictReader(csv_file)
                if "event_database" in (row["applies_to"] or "")
            ]
        self.assertEqual(offenders, [])

    def test_systemd_units_use_narrow_kind(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))

        self.assertFalse([row["key"] for row in rows if row["kind"] == "template"])

        unit_rows = [row for row in rows if row["kind"] == "systemd_unit"]
        self.assertTrue(unit_rows)
        for row in unit_rows:
            payload_units = [part.strip() for part in row["payload"].split(";") if part.strip()]
            path_units = [part.strip() for part in row["path"].split(";") if part.strip()]
            self.assertTrue(payload_units)
            self.assertTrue(path_units)
            self.assertTrue(all(unit.endswith((".service", ".timer", ".path")) for unit in payload_units))
            self.assertTrue(all(path.endswith((".service", ".timer", ".path")) for path in path_units))
            self.assertIn("systemd", row["applies_to"])

        config_unit_artifact_keys = {
            row["key"]
            for row in rows
            if row["kind"] == "config"
            and (row["path"].endswith((".service", ".timer", ".path")) or "/systemd/" in row["path"])
            and "checked-in systemd" in row["note"].lower()
        }
        self.assertEqual(set(), config_unit_artifact_keys)

    def test_applies_to_uses_type_first_source_scopes(self):
        pattern = re.compile(r"(?:^|;)[0-9]{2}_source_")
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            offenders = [
                (row["key"], row["applies_to"])
                for row in csv.DictReader(csv_file)
                if pattern.search(row["applies_to"] or "")
            ]
        self.assertEqual(offenders, [])

    def test_model_input_output_fields_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        expected = {
            "OPTION_SYMBOL": ("identity_field", "option_symbol", "option_chain_state_source"),
            "DOLLAR_VOLUME": ("field", "dollar_volume", "m03_target_state_vector_data_acquisition"),
            "QUOTE_AVG_BID_SIZE": ("field", "avg_bid_size", "m03_target_state_vector_data_acquisition"),
            "QUOTE_AVG_ASK_SIZE": ("field", "avg_ask_size", "m03_target_state_vector_data_acquisition"),
            "QUOTE_SPREAD_BPS": ("field", "spread_bps", "m03_target_state_vector_data_acquisition"),
            "SNAPSHOT_TYPE": ("classification_field", "snapshot_type", "m09_option_expression_feature_generation"),
            "INFORMATION_ROLE_TYPE": ("classification_field", "information_role_type", "m10_event_risk_governor_data_acquisition"),
            "EVENT_CATEGORY_TYPE": ("classification_field", "event_category_type", "m10_event_risk_governor_data_acquisition"),
            "SCOPE_TYPE": ("classification_field", "scope_type", "m10_event_risk_governor_data_acquisition"),
            "REFERENCE_TYPE": ("classification_field", "reference_type", "m10_event_risk_governor_data_acquisition"),
            "EVENT_REFERENCE": ("path_field", "reference", "m10_event_risk_governor_data_acquisition"),
            "EVENT_CANONICAL_EVENT_ID": ("identity_field", "canonical_event_id", "m10_event_risk_governor_data_acquisition"),
            "EVENT_DEDUP_STATUS": ("classification_field", "dedup_status", "m10_event_risk_governor_data_acquisition"),
            "EVENT_SOURCE_PRIORITY": ("field", "source_priority", "m10_event_risk_governor_data_acquisition"),
            "EVENT_COVERAGE_REASON": ("text_field", "coverage_reason", "m10_event_risk_governor_data_acquisition"),
            "EVENT_COVERED_BY_EVENT_ID": ("identity_field", "covered_by_event_id", "m10_event_risk_governor_data_acquisition"),
            "QUOTE_BID_EXCHANGE": ("field", "bid_exchange", "option_chain_state_source"),
            "QUOTE_ASK_EXCHANGE": ("field", "ask_exchange", "option_chain_state_source"),
            "QUOTE_BID_CONDITION": ("field", "bid_condition", "option_chain_state_source"),
            "QUOTE_ASK_CONDITION": ("field", "ask_condition", "option_chain_state_source"),
        }
        for key, (kind, payload, applies_to) in expected.items():
            self.assertEqual(rows[key]["kind"], kind)
            self.assertEqual(rows[key]["payload"], payload)
            self.assertIn(applies_to, rows[key]["applies_to"])

        for key in ["SYMBOL", "DATA_TIMESTAMP", "BAR_OPEN", "BAR_VWAP"]:
            self.assertIn("m01_market_regime_data_acquisition", rows[key]["applies_to"])
        for key in ["ETF_SYMBOL", "ETF_HOLDING_SYMBOL", "SECTOR_TYPE"]:
            self.assertIn("m02_sector_context_data_acquisition", rows[key]["applies_to"])
        for key in ["EVENT_ID", "EVENT_TIME", "TITLE", "SOURCE_NAME"]:
            self.assertIn("m10_event_risk_governor_data_acquisition", rows[key]["applies_to"])
        self.assertNotIn("OPTION_CONTRACT_COUNT", rows)
        self.assertNotIn("OPTION_CONTRACTS", rows)
        self.assertNotIn("QUOTE_TIMESTAMP", rows)
        self.assertNotIn("IV_TIMESTAMP", rows)
        self.assertNotIn("GREEKS_TIMESTAMP", rows)

    def test_initial_data_kinds_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        by_key = {row["key"]: row for row in rows}
        data_kinds = {row["key"]: row for row in rows if row["kind"] == "data_kind"}
        data_features = {row["key"]: row for row in rows if row["kind"] == "data_feature"}
        data_derived = {row["key"]: row for row in rows if row["kind"] == "data_derived"}

        self.assertEqual(data_kinds, {})
        self.assertEqual(data_derived, {})
        self.assertEqual(
            set(data_features),
            {
                "M01_MARKET_REGIME_FEATURE_GENERATION",
                "M02_SECTOR_CONTEXT_FEATURE_GENERATION",
                "M03_TARGET_STATE_VECTOR_FEATURE_GENERATION",
                "M10_EVENT_RISK_GOVERNOR_FEATURE_GENERATION",
                "M09_OPTION_EXPRESSION_FEATURE_GENERATION",
            },
        )
        self.assertEqual(data_features["M01_MARKET_REGIME_FEATURE_GENERATION"]["payload"], "m01_market_regime_feature_generation")
        self.assertIn("data_feature/m01_market_regime_feature_generation", data_features["M01_MARKET_REGIME_FEATURE_GENERATION"]["path"])
        self.assertEqual(data_features["M02_SECTOR_CONTEXT_FEATURE_GENERATION"]["payload"], "m02_sector_context_feature_generation")
        self.assertIn("data_feature/m02_sector_context_feature_generation", data_features["M02_SECTOR_CONTEXT_FEATURE_GENERATION"]["path"])
        self.assertEqual(
            data_features["M03_TARGET_STATE_VECTOR_FEATURE_GENERATION"]["payload"],
            "m03_target_state_vector_feature_generation",
        )
        self.assertIn(
            "data_feature/m03_target_state_vector_feature_generation",
            data_features["M03_TARGET_STATE_VECTOR_FEATURE_GENERATION"]["path"],
        )
        self.assertEqual(data_features["M10_EVENT_RISK_GOVERNOR_FEATURE_GENERATION"]["payload"], "m10_event_risk_governor_feature_generation")
        self.assertIn("data_feature/m10_event_risk_governor_feature_generation", data_features["M10_EVENT_RISK_GOVERNOR_FEATURE_GENERATION"]["path"])
        self.assertEqual(data_features["M09_OPTION_EXPRESSION_FEATURE_GENERATION"]["payload"], "m09_option_expression_feature_generation")
        self.assertIn("data_feature/m09_option_expression_feature_generation", data_features["M09_OPTION_EXPRESSION_FEATURE_GENERATION"]["path"])
        self.assertIn("trading-data", data_features["M01_MARKET_REGIME_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("market_regime_model", data_features["M01_MARKET_REGIME_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("m01_market_regime_data_acquisition", data_features["M01_MARKET_REGIME_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("sector_context_model", data_features["M02_SECTOR_CONTEXT_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("m01_market_regime_data_acquisition", data_features["M02_SECTOR_CONTEXT_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("model_03_target_state_vector", data_features["M03_TARGET_STATE_VECTOR_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("target_state_vector_model", data_features["M03_TARGET_STATE_VECTOR_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("m10_event_risk_governor_data_acquisition", data_features["M10_EVENT_RISK_GOVERNOR_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("event_risk_governor", data_features["M10_EVENT_RISK_GOVERNOR_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("option_chain_state_source", data_features["M09_OPTION_EXPRESSION_FEATURE_GENERATION"]["applies_to"])
        self.assertIn("option_expression_model", data_features["M09_OPTION_EXPRESSION_FEATURE_GENERATION"]["applies_to"])
        self.assertNotIn("feature_snapshots", data_features["M01_MARKET_REGIME_FEATURE_GENERATION"]["applies_to"])
        for row in rows:
            self.assertNotIn("trading-source/storage/templates/data_kinds", row["path"])
        for deleted_preview_key in {
            "MACRO_RELEASE_EVENT",
            "GDELT_ARTICLE",
            "TRADING_ECONOMICS_CALENDAR_EVENT",
            "EQUITY_BAR",
            "EQUITY_LIQUIDITY_BAR",
            "CRYPTO_BAR",
            "CRYPTO_LIQUIDITY_BAR",
            "OPTION_ACTIVITY_EVENT",
            "OPTION_ACTIVITY_EVENT_DETAIL",
            "OPTION_BAR",
            "OPTION_CHAIN_SNAPSHOT",
            "ETF_HOLDINGS_SNAPSHOT",
            "STOCK_ETF_EXPOSURE",
            "EQUITY_ABNORMAL_ACTIVITY_EVENT",
            "TRADING_EVENT",
            "EVENT_FACTOR",
            "EVENT_ANALYSIS_REPORT",
            "DATA_KIND_TEMPLATE_GENERATOR",
            "DATA_KIND_TEMPLATE_PREVIEW_FILE_PATH",
        }:
            self.assertNotIn(deleted_preview_key, by_key)
        reclassified_data_kind_keys = {
            "ETF_CONSTITUENT_WEIGHT",
            "ETF_FUND_METADATA",
            "SEC_FILING_DOCUMENT",
            "CRYPTO_TRADE",
            "CRYPTO_QUOTE",
            "CRYPTO_ORDER_BOOK",
            "EQUITY_TRADE",
            "EQUITY_QUOTE",
            "EQUITY_SNAPSHOT",
            "OPTION_GREEKS_FIRST_ORDER",
            "OPTION_GREEKS_SECOND_ORDER",
            "OPTION_GREEKS_THIRD_ORDER",
            "OPTION_IMPLIED_VOLATILITY",
            "OPTION_TRADE_GREEKS",
            "OPTION_TRADE",
            "OPTION_QUOTE",
            "OPTION_NBBO",
            "SEC_COMPANY_FACT",
        }
        for key in reclassified_data_kind_keys:
            self.assertIn(key, by_key)
            self.assertNotEqual(by_key[key]["kind"], "data_kind")

        self.assertEqual(by_key["SNAPSHOT_TIME"]["kind"], "temporal_field")
        self.assertEqual(by_key["SNAPSHOT_TIME"]["payload"], "snapshot_time")
        self.assertIn("option_chain_state_source", by_key["SNAPSHOT_TIME"]["applies_to"])
        self.assertIn("m01_market_regime_feature_generation", by_key["SNAPSHOT_TIME"]["applies_to"])
        self.assertNotIn("feature_snapshots", by_key["SNAPSHOT_TIME"]["applies_to"])
        payloads = {row["payload"] for row in rows}
        for generated_feature_column in {"spy_return_30m", "spy_return_1d", "spy_return_5d", "spy_return_20d"}:
            self.assertNotIn(generated_feature_column, payloads)

        deleted_deprecated_macro_keys = {
            "MACRO_BEA_FIXED_ASSETS",
            "MACRO_ALFRED_VINTAGE",
            "MACRO_BEA_NIPA",
            "MACRO_BLS_CPI",
            "MACRO_BLS_ECI",
            "MACRO_FRED_NATIVE",
            "MACRO_RELEASE",
            "MACRO_TREASURY_DTS",
            "MACRO_TREASURY_MTS",
        }
        for key in deleted_deprecated_macro_keys:
            self.assertNotIn(key, by_key)

        expected_feed_capabilities = {
            "ALPACA_EQUITY_BAR",
            "ALPACA_EQUITY_NEWS",
            "ALPACA_EQUITY_LATEST_SNAPSHOT",
            "CRYPTO_TRADE",
            "CRYPTO_QUOTE",
            "CRYPTO_ORDER_BOOK",
            "OKX_CRYPTO_CANDLE",
            "EQUITY_TRADE",
            "EQUITY_QUOTE",
            "EQUITY_SNAPSHOT",
            "ETF_ISSUER_HOLDINGS",
            "GDELT_GKG_RECORD",
            "OPTION_GREEKS_FIRST_ORDER",
            "OPTION_GREEKS_SECOND_ORDER",
            "OPTION_GREEKS_THIRD_ORDER",
            "OPTION_IMPLIED_VOLATILITY",
            "OPTION_TRADE_GREEKS",
            "OPTION_TRADE",
            "OPTION_QUOTE",
            "OPTION_NBBO",
            "SEC_COMPANY_FACT",
            "SEC_FILING_DOCUMENT",
            "TRADING_ECONOMICS_CALENDAR_STORAGE_SOURCE",
        }
        for key in expected_feed_capabilities:
            self.assertEqual(by_key[key]["kind"], "feed_capability")
        self.assertIn("01_feed_alpaca_bars", by_key["ALPACA_EQUITY_BAR"]["applies_to"])
        self.assertIn("03_feed_alpaca_news", by_key["ALPACA_EQUITY_NEWS"]["applies_to"])
        self.assertIn("02_feed_alpaca_liquidity", by_key["ALPACA_EQUITY_LATEST_SNAPSHOT"]["applies_to"])
        self.assertIn("05_feed_gdelt_news", by_key["GDELT_GKG_RECORD"]["applies_to"])
        self.assertIn("06_feed_etf_holdings", by_key["ETF_ISSUER_HOLDINGS"]["applies_to"])
        self.assertIn("07_feed_trading_economics_calendar_web", by_key["TRADING_ECONOMICS_CALENDAR_STORAGE_SOURCE"]["applies_to"])
        for obsolete_calendar_or_macro_key in {
            "CALENDAR_DISCOVERY",
            "ECONOMIC_RELEASE_CALENDAR",
            "EQUITY_EARNINGS_CALENDAR",
            "FOMC_MEETING",
            "FOMC_MINUTES",
            "FOMC_SEP",
            "FOMC_STATEMENT",
            "MACRO_RELEASE_CALENDAR",
            "ECONOMIC_RELEASE_EVENT",
            "FOMC_CALENDAR",
            "NASDAQ_EARNINGS_CALENDAR",
            "BEA_SECRET_ALIAS",
            "BLS_SECRET_ALIAS",
            "CENSUS_SECRET_ALIAS",
            "FRED_SECRET_ALIAS",
        }:
            self.assertNotIn(obsolete_calendar_or_macro_key, by_key)
        self.assertNotIn("MACRO_RELEASE", by_key)

    def test_layer_one_artifact_chain_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        expected = {
            "M01_MARKET_REGIME_DATA_ACQUISITION": ("data_source", "m01_market_regime_data_acquisition"),
            "M01_MARKET_REGIME_FEATURE_GENERATION": ("data_feature", "m01_market_regime_feature_generation"),
            "MODEL_01_MARKET_REGIME": ("term", "m01_market_regime_model_generation"),
            "MODEL_01_MARKET_REGIME_EXPLAINABILITY": ("term", "m01_market_regime_model_generation_explainability"),
            "MODEL_01_MARKET_REGIME_DIAGNOSTICS": ("term", "m01_market_regime_model_generation_diagnostics"),
        }
        for key, (kind, payload) in expected.items():
            self.assertEqual(rows[key]["kind"], kind)
            self.assertEqual(rows[key]["payload"], payload)

        self.assertIn("m01_market_regime_model_generation", rows["MODEL_01_MARKET_REGIME_EXPLAINABILITY"]["applies_to"])
        self.assertIn("m01_market_regime_model_generation", rows["MODEL_01_MARKET_REGIME_DIAGNOSTICS"]["applies_to"])

    def test_market_regime_etf_universe_shared_csv_columns_are_registered(self):
        shared_path = Path("/root/projects/trading-storage/main/shared/layer_01_02_market_context_etf_universe.csv")
        with shared_path.open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 31)
        self.assertEqual(
            list(rows[0].keys()),
            ["symbol", "universe_type", "model_layer", "exposure_type", "feature_grain", "fund_name", "issuer_name", "interpretation"],
        )
        self.assertEqual(rows[0]["symbol"], "BITW")
        self.assertEqual(rows[0]["model_layer"], "layer_01_market_regime")
        self.assertEqual({row["model_layer"] for row in rows}, {"layer_01_market_regime", "layer_02_sector_context"})
        layer_two_symbols = {row["symbol"] for row in rows if row["model_layer"] == "layer_02_sector_context"}
        self.assertEqual(
            layer_two_symbols,
            {"BKCH", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"},
        )
        self.assertIn("RSP", {row["symbol"] for row in rows})
        self.assertIn("SHY", {row["symbol"] for row in rows})
        self.assertIn("IEF", {row["symbol"] for row in rows})
        self.assertNotIn("SMH", {row["symbol"] for row in rows})
        self.assertNotIn("AIQ", {row["symbol"] for row in rows})
        self.assertIn("BKCH", {row["symbol"] for row in rows})
        self.assertNotIn("IBIT", {row["symbol"] for row in rows})
        self.assertNotIn("ETHA", {row["symbol"] for row in rows})
        self.assertNotIn("FSOL", {row["symbol"] for row in rows})
        self.assertEqual(rows[-1]["symbol"], "VIXY")

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registry = {row["key"]: row for row in csv.DictReader(csv_file)}
        self.assertEqual(registry["MARKET_REGIME_ETF_UNIVERSE_SHARED_CSV"]["payload"], "trading-storage/main/shared/layer_01_02_market_context_etf_universe.csv")
        self.assertEqual(registry["MARKET_REGIME_ETF_UNIVERSE_SHARED_CSV"]["path"], "/root/projects/trading-storage/main/shared/layer_01_02_market_context_etf_universe.csv")
        expected_fields = {
            "SYMBOL": "symbol",
            "UNIVERSE_TYPE": "universe_type",
            "MODEL_LAYER": "model_layer",
            "EXPOSURE_TYPE": "exposure_type",
            "FEATURE_GRAIN": "feature_grain",
            "FUND_NAME": "fund_name",
            "ISSUER_NAME": "issuer_name",
            "INTERPRETATION": "interpretation",
        }
        classification_fields = {"UNIVERSE_TYPE", "MODEL_LAYER", "EXPOSURE_TYPE"}
        self.assertEqual(registry["MODEL_LAYER_LAYER_01_MARKET_REGIME"]["kind"], "term")
        self.assertEqual(registry["MODEL_LAYER_LAYER_01_MARKET_REGIME"]["payload"], "layer_01_market_regime")
        self.assertEqual(registry["MODEL_LAYER_LAYER_02_SECTOR_CONTEXT"]["kind"], "term")
        self.assertEqual(registry["MODEL_LAYER_LAYER_02_SECTOR_CONTEXT"]["payload"], "layer_02_sector_context")
        identity_fields = {"SYMBOL", "FUND_NAME", "ISSUER_NAME"}
        text_fields = {"INTERPRETATION"}
        for key, payload in expected_fields.items():
            expected_kind = "classification_field" if key in classification_fields else "identity_field" if key in identity_fields else "text_field" if key in text_fields else "field"
            self.assertEqual(registry[key]["kind"], expected_kind)
            self.assertEqual(registry[key]["payload"], payload)
            self.assertIn("market_regime_etf_universe", registry[key]["applies_to"])
            if key not in {"SYMBOL", "ISSUER_NAME", "INTERPRETATION"}:
                self.assertEqual(registry[key]["path"], "trading-storage/main/shared/layer_01_02_market_context_etf_universe.csv")

    def test_market_regime_relative_strength_combinations_shared_csv_is_registered(self):
        shared_path = Path("/root/projects/trading-storage/main/shared/layer_01_02_market_context_relative_strength_combinations.csv")
        with shared_path.open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 39)
        self.assertEqual(
            list(rows[0].keys()),
            [
                "combination_id",
                "combination_type",
                "model_layer",
                "numerator_symbol",
                "denominator_symbol",
                "numerator_bar_grain",
                "denominator_bar_grain",
                "feature_bar_grain",
                "interpretation",
            ],
        )
        by_id = {row["combination_id"]: row for row in rows}
        self.assertEqual(by_id["rsp_spy"]["feature_bar_grain"], "1m")
        self.assertEqual(by_id["rsp_spy"]["model_layer"], "layer_01_market_regime")
        self.assertEqual({row["model_layer"] for row in rows}, {"layer_01_market_regime", "layer_02_sector_context"})
        self.assertEqual(by_id["tlt_shy"]["combination_type"], "primary")
        self.assertEqual(by_id["ief_shy"]["combination_type"], "primary")
        self.assertEqual(by_id["xlk_spy"]["combination_type"], "sector_rotation")
        self.assertNotIn("smh_xlk", by_id)
        self.assertNotIn("aiq_qqq", by_id)
        self.assertEqual(by_id["bkch_bitw"]["model_layer"], "layer_02_sector_context")
        self.assertEqual(by_id["bkch_bitw"]["combination_type"], "sector_rotation")
        self.assertNotIn("ibit_bitw", by_id)
        self.assertNotIn("etha_bitw", by_id)
        self.assertNotIn("fsol_bitw", by_id)

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registry = {row["key"]: row for row in csv.DictReader(csv_file)}
        self.assertEqual(
            registry["MARKET_REGIME_RELATIVE_STRENGTH_COMBINATIONS_SHARED_CSV"]["payload"],
            "trading-storage/main/shared/layer_01_02_market_context_relative_strength_combinations.csv",
        )
        self.assertEqual(
            registry["MARKET_REGIME_RELATIVE_STRENGTH_COMBINATIONS_SHARED_CSV"]["path"],
            "/root/projects/trading-storage/main/shared/layer_01_02_market_context_relative_strength_combinations.csv",
        )
        expected_fields = {
            "COMBINATION_ID": ("identity_field", "combination_id"),
            "COMBINATION_TYPE": ("classification_field", "combination_type"),
            "MODEL_LAYER": ("classification_field", "model_layer"),
            "NUMERATOR_SYMBOL": ("identity_field", "numerator_symbol"),
            "DENOMINATOR_SYMBOL": ("identity_field", "denominator_symbol"),
            "NUMERATOR_BAR_GRAIN": ("field", "numerator_bar_grain"),
            "DENOMINATOR_BAR_GRAIN": ("field", "denominator_bar_grain"),
            "FEATURE_BAR_GRAIN": ("field", "feature_bar_grain"),
            "INTERPRETATION": ("text_field", "interpretation"),
        }
        for key, (kind, payload) in expected_fields.items():
            self.assertEqual(registry[key]["kind"], kind)
            self.assertEqual(registry[key]["payload"], payload)
            if key not in {"INTERPRETATION", "MODEL_LAYER"}:
                self.assertEqual(registry[key]["path"], "trading-storage/main/shared/layer_01_02_market_context_relative_strength_combinations.csv")
            self.assertIn("market_regime_relative_strength_combinations", registry[key]["applies_to"])

    def test_equity_total_symbol_pool_route_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registry = {row["key"]: row for row in csv.DictReader(csv_file)}

        artifact = registry["EQUITY_TOTAL_SYMBOL_POOL_SHARED_CSV"]
        self.assertEqual(artifact["kind"], "shared_artifact")
        self.assertEqual(artifact["payload"], "trading-storage/main/shared/equity_total_symbol_pool.csv")
        self.assertEqual(artifact["path"], "/root/projects/trading-storage/main/shared/equity_total_symbol_pool.csv")
        self.assertIn("calendar_maintenance", artifact["applies_to"])
        self.assertIn("active inactive membership evidence", artifact["note"])

        historical_artifact = registry["HISTORICAL_CANDIDATE_UNIVERSE_SHARED_CSV"]
        self.assertEqual(historical_artifact["kind"], "shared_artifact")
        self.assertEqual(historical_artifact["payload"], "trading-storage/main/shared/historical_candidate_universe.csv")
        self.assertIn("historical_candidate_universe", historical_artifact["applies_to"])
        self.assertIn("crypto_context_anchor", historical_artifact["applies_to"])
        self.assertIn("not point-in-time historical", historical_artifact["note"])

        script = registry["BUILD_EQUITY_TOTAL_SYMBOL_POOL"]
        self.assertEqual(script["kind"], "script")
        self.assertEqual(script["path"], "trading-data/scripts/data/build_equity_total_symbol_pool.py")
        self.assertIn("tradingview_screener_snapshot", script["applies_to"])
        self.assertIn("preserves observed inactive rows", script["note"])

        historical_script = registry["BUILD_HISTORICAL_CANDIDATE_UNIVERSE"]
        self.assertEqual(historical_script["kind"], "script")
        self.assertEqual(historical_script["path"], "trading-data/scripts/data/build_historical_candidate_universe.py")
        self.assertIn("historical_candidate_universe", historical_script["applies_to"])
        self.assertIn("crypto_spot", historical_script["applies_to"])

        fetch_script = registry["FETCH_TRADINGVIEW_EQUITY_SCREENER"]
        self.assertEqual(fetch_script["kind"], "script")
        self.assertEqual(fetch_script["path"], "trading-data/scripts/data/fetch_tradingview_equity_screener.py")
        self.assertIn("dollar_volume_rank", fetch_script["applies_to"])

        refresh_script = registry["REFRESH_EQUITY_TOTAL_SYMBOL_POOL_FROM_TRADINGVIEW"]
        self.assertEqual(refresh_script["kind"], "script")
        self.assertIn("uncertain optionability", refresh_script["note"])

    def test_target_layer2_context_mapping_shared_csv_is_registered(self):
        shared_path = Path("/root/projects/trading-storage/main/shared/layer_02_target_context_mapping.csv")
        with shared_path.open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            list(rows[0].keys()),
            [
                "target_symbol",
                "target_asset_class",
                "spot_ref",
                "layer2_context_symbol",
                "layer2_mapping_method_type",
                "listed_proxy_symbol",
                "optionable_proxy_symbol",
                "optionable_proxy_status",
                "proxy_role_type",
                "proxy_use",
                "review_status",
                "interpretation",
            ],
        )
        by_target: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            by_target.setdefault(row["target_symbol"], []).append(row)
        self.assertEqual(set(by_target), {"BTC", "ETH", "SOL", "AAPL", "AAOI"})
        self.assertEqual(by_target["BTC"][0]["layer2_context_symbol"], "BKCH")
        self.assertEqual(by_target["BTC"][0]["listed_proxy_symbol"], "IBIT")
        self.assertEqual(by_target["BTC"][0]["optionable_proxy_status"], "accepted_optionable_proxy")
        self.assertEqual(by_target["ETH"][0]["optionable_proxy_status"], "verify_before_option_use")
        self.assertEqual(by_target["SOL"][0]["optionable_proxy_status"], "verify_before_option_use")
        self.assertEqual(by_target["AAPL"][0]["layer2_context_symbol"], "XLK")
        self.assertEqual(by_target["AAPL"][0]["layer2_mapping_method_type"], "primary_sector_context")
        self.assertEqual(by_target["AAPL"][0]["proxy_role_type"], "no_auxiliary_proxy_type")
        self.assertEqual(
            {row["layer2_context_symbol"] for row in by_target["AAOI"]},
            {"XLK", "XLC"},
        )
        self.assertEqual(
            {row["layer2_mapping_method_type"] for row in by_target["AAOI"]},
            {
                "primary_sector_context",
                "weak_demand_side_context",
            },
        )

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registry = {row["key"]: row for row in csv.DictReader(csv_file)}
        self.assertEqual(
            registry["TARGET_LAYER2_CONTEXT_MAPPING_SHARED_CSV"]["payload"],
            "trading-storage/main/shared/layer_02_target_context_mapping.csv",
        )
        self.assertEqual(
            registry["TARGET_LAYER2_CONTEXT_MAPPING_SHARED_CSV"]["path"],
            "/root/projects/trading-storage/main/shared/layer_02_target_context_mapping.csv",
        )
        self.assertEqual(registry["TARGET_LAYER2_CONTEXT_MAPPING"]["payload"], "target_layer2_context_mapping")
        self.assertIn("target_context_sector_anchor_mapping", registry["TARGET_LAYER2_CONTEXT_MAPPING"]["applies_to"])
        self.assertEqual(registry["TARGET_CONTEXT_SECTOR_ANCHOR_MAPPING"]["payload"], "target_context_sector_anchor_mapping")
        self.assertEqual(registry["TARGET_CONTEXT_MULTI_ROW_BY_TARGET"]["payload"], "target_context_multi_row_by_target")
        self.assertEqual(registry["TARGET_SYMBOL"]["payload"], "target_symbol")
        self.assertIn("target_layer2_context_mapping", registry["TARGET_SYMBOL"]["applies_to"])
        self.assertEqual(registry["INTERPRETATION"]["payload"], "interpretation")
        self.assertIn("target_layer2_context_mapping", registry["INTERPRETATION"]["applies_to"])
        expected_fields = {
            "TARGET_LAYER2_CONTEXT_TARGET_ASSET_CLASS": ("classification_field", "target_asset_class"),
            "TARGET_LAYER2_CONTEXT_SPOT_REF": ("identity_field", "spot_ref"),
            "TARGET_LAYER2_CONTEXT_SYMBOL": ("identity_field", "layer2_context_symbol"),
            "TARGET_LAYER2_MAPPING_METHOD_TYPE": ("classification_field", "layer2_mapping_method_type"),
            "TARGET_LISTED_PROXY_SYMBOL": ("identity_field", "listed_proxy_symbol"),
            "TARGET_OPTIONABLE_PROXY_SYMBOL": ("identity_field", "optionable_proxy_symbol"),
            "TARGET_OPTIONABLE_PROXY_STATUS": ("classification_field", "optionable_proxy_status"),
            "TARGET_PROXY_ROLE_TYPE": ("classification_field", "proxy_role_type"),
            "TARGET_PROXY_USE": ("text_field", "proxy_use"),
            "TARGET_LAYER2_CONTEXT_REVIEW_STATUS": ("classification_field", "review_status"),
        }
        for key, (kind, payload) in expected_fields.items():
            self.assertEqual(registry[key]["kind"], kind)
            self.assertEqual(registry[key]["payload"], payload)
            self.assertEqual(registry[key]["path"], "trading-storage/main/shared/layer_02_target_context_mapping.csv")
            self.assertIn("target_layer2_context_mapping", registry[key]["applies_to"])

    def test_target_context_agent_review_script_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registry = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(registry["TARGET_LAYER2_CONTEXT_AGENT_REVIEW"]["payload"], "target_layer2_context_agent_review")
        self.assertEqual(
            registry["TARGET_LAYER2_CONTEXT_AGENT_REVIEW_REQUEST"]["payload"],
            "target_layer2_context_agent_review_request",
        )
        self.assertEqual(
            registry["TARGET_LAYER2_CONTEXT_AGENT_REVIEW_DECISION"]["payload"],
            "target_layer2_context_agent_review_decision",
        )
        self.assertEqual(registry["REVIEW_TARGET_LAYER2_CONTEXT_MAPPING"]["kind"], "script")
        self.assertEqual(
            registry["REVIEW_TARGET_LAYER2_CONTEXT_MAPPING"]["path"],
            "/root/projects/trading-manager/scripts/tasks/review_target_layer2_context_mapping.py",
        )
        self.assertIn("target_layer2_context_agent_review", registry["REVIEW_TARGET_LAYER2_CONTEXT_MAPPING"]["applies_to"])
        self.assertIn("no_provider_calls", registry["TARGET_LAYER2_CONTEXT_AGENT_REVIEW_SAFETY_BOUNDARY"]["payload"])

    def test_registered_payload_formats_match_sql_constraint(self):
        schema = Path("scripts/registry/sql/trading_registry.sql").read_text()
        constraint = re.search(
            r"CONSTRAINT trading_registry_payload_format_check\s+CHECK \(payload_format IN \((.*?)\)\);",
            schema,
            re.S,
        ).group(1)
        constrained_formats = tuple(re.findall(r"'([^']+)'", constraint))

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registered_formats = tuple(
                row["payload"]
                for row in csv.DictReader(csv_file)
                if row["kind"] == "payload_format"
            )

        self.assertEqual(sorted(registered_formats), sorted(constrained_formats))
        self.assertIn("iso_time", registered_formats)
        self.assertIn("iso_datetime", registered_formats)
        self.assertIn("secret_alias", registered_formats)

    def test_status_like_rows_use_one_kind_with_domain_scope(self):
        old_status_kinds = {
            "task_lifecycle_status",
            "review_status",
            "acceptance_status",
            "test_status",
            "maintenance_status",
            "docs_status",
            "artifact_sync_policy",
        }
        retired_unaccepted_slot_status_domains = {
            "acceptance_status",
            "task_lifecycle_status",
            "review_status",
            "test_status",
            "maintenance_status",
            "docs_status",
        }
        expected_domains = {
            "agent_model_promotion_decision",
            "artifact_sync_policy_type",
            "anonymous_target_candidate_builder",
            "manager_contract_lifecycle_status",
            "manager_request",
            "promotion_result",
            "rolling_fold_promotion_task",
            "run_manifest",
            "run_step",
            "artifact_ref",
            "candidate_anonymity_check_state",
            "candidate_eligibility_state",
            "candidate_generation_reason_codes",
            "earnings_guidance_event_family",
            "event_family_remaining_acceptance",
            "event_lifecycle_stage",
            "event_release_phase",
            "event_failure_risk_vector",
            "event_family_bias_association_packet",
            "event_family_prior_role",
            "event_family_scouting_packet",
            "event_instance_observation_role",
            "execution_model_decision_input_handoff_status",
            "fold_scoped_source_data",
            "feature_consumption_contract",
            "detector_run",
            "event_schedule_type",
            "event_temporal_form",
            "layer_04_event_failure_risk",
            "layer_4_projection_type",
            "layer_4_state_overlay",
            "layer_4_state_overlay_candidate",
            "layer4_event_feature_policy",
            "layer_10_event_risk_governor",
            "layer_10_fold_completion",
            "layer_10_fold_completion_summary",
            "manager_layer_ten_event_risk_governor_input_materialization",
            "focus_pool_status",
            "model_realtime_decision_component_route_status",
            "model_realtime_decision_route_plan_readiness",
            "ready_signal",
            "one_shot_replay_acquisition",
            "production_completion_status",
            "production_route_decision",
            "production_route_review_status",
            "quarantine_candidate",
            "replay_dataset_preparation",
            "replay_freeze_gate",
            "retention_class",
            "storage_lifecycle",
            "state_signal_type",
            "target_state_vector_model",
            "temporal_attention_pool",
            "temporal_attention_focus_pool",
            "trading-storage",
            "window_policy",
            "cross_fold_stability_role",
        }

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertNotIn("event_attention_pool", Path("scripts/registry/current.csv").read_text(encoding="utf-8"))

        self.assertFalse({row["kind"] for row in rows} & old_status_kinds)
        status_rows = [row for row in rows if row["kind"] == "status_value"]
        self.assertTrue(status_rows)
        domains = {
            domain
            for row in status_rows
            for domain in row["applies_to"].split(";")
            if domain
        }
        self.assertEqual(domains, expected_domains)
        self.assertFalse(domains & retired_unaccepted_slot_status_domains)
        scoped_payloads = [
            (row["applies_to"], row["payload"])
            for row in status_rows
        ]
        self.assertEqual(len(scoped_payloads), len(set(scoped_payloads)))
        self.assertEqual(
            next(row for row in status_rows if row["payload"] == "registry_only")["key"],
            "ARTIFACT_SYNC_POLICY_TYPE_REGISTRY_ONLY",
        )

    def test_temporal_fields_are_separate_and_iso_scoped(self):
        expected_temporal_keys = {
            "AS_OF_DATE",
            "DATA_TIMESTAMP",
            "EVENT_TIME",
            "OPTION_EXPIRATION",
            "REGISTRY_ITEM_CREATED_AT",
            "REGISTRY_ITEM_UPDATED_AT",
            "SNAPSHOT_TIME",
            "AVAILABLE_TIME",
            "TRADEABLE_TIME",
            "UNDERLYING_TIMESTAMP",
        }
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in expected_temporal_keys:
            self.assertEqual(rows[key]["kind"], "temporal_field")
            self.assertEqual(rows[key]["payload_format"], "field_name")
            self.assertIn("ISO 8601", rows[key]["note"])
            self.assertFalse(rows[key]["key"].endswith("_ET"))
            self.assertFalse(rows[key]["key"].endswith("_UTC"))
            self.assertFalse(rows[key]["payload"].endswith("_et"))
            self.assertFalse(rows[key]["payload"].endswith("_utc"))
        self.assertNotIn("TIMELINE_CREATED_AT_ET", rows)
        self.assertNotIn("TIMELINE_UPDATED_AT_ET", rows)
        self.assertNotIn("OPTION_EVENT_DETAIL_STANDARD_GENERATED_AT", rows)
        self.assertNotIn("GENERATED_AT", rows)
        self.assertEqual(rows["REGISTRY_ITEM_CREATED_AT"]["applies_to"], "trading_registry")
        self.assertEqual(rows["REGISTRY_ITEM_UPDATED_AT"]["applies_to"], "trading_registry")
        self.assertEqual(rows["TIMEFRAME"]["kind"], "field")
        self.assertEqual(rows["OPTION_DAYS_TO_EXPIRATION"]["kind"], "field")
        self.assertIn("model_03_target_state_vector", rows["AVAILABLE_TIME"]["applies_to"])
        self.assertIn("target_state_vector_model", rows["TRADEABLE_TIME"]["applies_to"])

    def test_field_like_payloads_are_unique_semantic_words(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registry_rows = list(csv.DictReader(csv_file))
            field_like_rows = [
                row
                for row in registry_rows
                if row["kind"] in {"field", "identity_field", "path_field", "temporal_field", "classification_field", "text_field", "parameter_field"}
            ]
            state_vector_value_rows = [row for row in registry_rows if row["kind"] == "state_vector_value"]

        payloads = [row["payload"] for row in field_like_rows]
        self.assertEqual(len(payloads), len(set(payloads)))

        retired_unaccepted_slot_scopes = {
            "acceptance_receipt_slots",
            "completion_receipt_slots",
            "execution_key_slots",
            "maintenance_output_slots",
            "task_register_slots",
        }
        for row in field_like_rows:
            self.assertNotIn("trading-source/storage/templates/data_kinds", row["path"])
            applies_to = set(filter(None, row["applies_to"].split(";")))
            self.assertFalse({part for part in applies_to if part.endswith("_template")})
            self.assertNotIn("option_template", applies_to)
            self.assertNotIn("data_kind_template", applies_to)
            self.assertFalse(applies_to & retired_unaccepted_slot_scopes)

        by_key = {row["key"]: row for row in field_like_rows}
        expected_bar_fields = {
            "BAR_OPEN": "bar_open",
            "BAR_HIGH": "bar_high",
            "BAR_LOW": "bar_low",
            "BAR_CLOSE": "bar_close",
            "BAR_VOLUME": "bar_volume",
            "BAR_VWAP": "bar_vwap",
            "BAR_TRADE_COUNT": "bar_trade_count",
        }
        for key, payload in expected_bar_fields.items():
            self.assertIn("m01_market_regime_data_acquisition", by_key[key]["applies_to"])
            self.assertIn("m03_target_state_vector_data_acquisition", by_key[key]["applies_to"])
            self.assertIn("m09_option_expression_data_acquisition_contract_path", by_key[key]["applies_to"])
            self.assertEqual(by_key[key]["payload"], payload)
        self.assertEqual(by_key["TIMEFRAME"]["payload"], "timeframe")
        self.assertEqual(by_key["TARGET_CANDIDATE_ID"]["kind"], "identity_field")
        self.assertIn("model_03_target_state_vector", by_key["TARGET_CANDIDATE_ID"]["applies_to"])
        target_state_fields = {
            "TARGET_CONTEXT_STATE_VERSION": "target_context_state_version",
            "MARKET_CONTEXT_STATE_REF": "market_context_state_ref",
            "SECTOR_CONTEXT_STATE_REF": "sector_context_state_ref",
            "TARGET_CONTEXT_STATE_REF": "target_context_state_ref",
            "SOURCE_RUN_REF": "source_run_ref",
            "RUN_ID": "run_id",
        }
        for key, payload in target_state_fields.items():
            self.assertEqual(by_key[key]["payload"], payload)
        self.assertIn("m03_target_state_vector_feature_generation", by_key["RUN_ID"]["applies_to"])

        state_vector_values = {row["key"]: row for row in state_vector_value_rows}
        expected_state_vector_values = {
            "BREADTH_PARTICIPATION_SCORE": "1_breadth_participation_score",
            "CORRELATION_CROWDING_SCORE": "1_correlation_crowding_score",
            "DISPERSION_OPPORTUNITY_SCORE": "1_dispersion_opportunity_score",
            "MARKET_DIRECTION_SCORE": "1_market_direction_score",
            "MARKET_DIRECTION_STRENGTH_SCORE": "1_market_direction_strength_score",
            "MARKET_LIQUIDITY_PRESSURE_SCORE": "1_market_liquidity_pressure_score",
            "MARKET_LIQUIDITY_SUPPORT_SCORE": "1_market_liquidity_support_score",
            "MARKET_RISK_STRESS_SCORE": "1_market_risk_stress_score",
            "MARKET_STABILITY_SCORE": "1_market_stability_score",
            "MARKET_TRANSITION_RISK_SCORE": "1_market_transition_risk_score",
            "MARKET_TREND_QUALITY_SCORE": "1_market_trend_quality_score",
            "MARKET_CONTEXT_SUPPORT_SCORE": "2_market_context_support_score",
            "SECTOR_BREADTH_CONFIRMATION_SCORE": "2_sector_breadth_confirmation_score",
            "SECTOR_CROWDING_RISK_SCORE": "2_sector_crowding_risk_score",
            "SECTOR_INTERNAL_DISPERSION_SCORE": "2_sector_internal_dispersion_score",
            "SECTOR_LIQUIDITY_TRADABILITY_SCORE": "2_sector_liquidity_tradability_score",
            "SECTOR_RELATIVE_DIRECTION_SCORE": "2_sector_relative_direction_score",
            "SECTOR_TRADABILITY_SCORE": "2_sector_tradability_score",
            "SECTOR_TRANSITION_RISK_SCORE": "2_sector_transition_risk_score",
            "SECTOR_TREND_QUALITY_SCORE": "2_sector_trend_quality_score",
            "SECTOR_TREND_STABILITY_SCORE": "2_sector_trend_stability_score",
            "CONTEXT_DIRECTION_ALIGNMENT_SCORE_BY_WINDOW": "3_context_direction_alignment_score_<window>",
            "CONTEXT_SUPPORT_QUALITY_SCORE_BY_WINDOW": "3_context_support_quality_score_<window>",
            "TARGET_DIRECTION_SCORE_BY_WINDOW": "3_target_direction_score_<window>",
            "TARGET_DIRECTION_STRENGTH_SCORE_BY_WINDOW": "3_target_direction_strength_score_<window>",
            "TARGET_EXHAUSTION_RISK_SCORE_BY_WINDOW": "3_target_exhaustion_risk_score_<window>",
            "TARGET_LIQUIDITY_TRADABILITY_SCORE": "3_target_liquidity_tradability_score",
            "TARGET_NOISE_SCORE_BY_WINDOW": "3_target_noise_score_<window>",
            "TARGET_PATH_STABILITY_SCORE_BY_WINDOW": "3_target_path_stability_score_<window>",
            "TARGET_STATE_PERSISTENCE_SCORE_BY_WINDOW": "3_target_state_persistence_score_<window>",
            "TARGET_STATE_TRADABILITY_SCORE_BY_WINDOW": "3_tradability_score_<window>",
            "TARGET_TRANSITION_RISK_SCORE_BY_WINDOW": "3_target_transition_risk_score_<window>",
            "TARGET_TREND_QUALITY_SCORE_BY_WINDOW": "3_target_trend_quality_score_<window>",
            "TARGET_HANDOFF_STATE": "3_target_handoff_state",
            "TARGET_HANDOFF_BIAS": "3_target_handoff_bias",
            "TARGET_HANDOFF_RANK": "3_target_handoff_rank",
            "TARGET_SELECTION_REASON_CODES": "3_target_selection_reason_codes",
            "TARGET_OPTION_CHAIN_STATE": "target_option_chain_state",
            "TARGET_OPTION_FLOW_PRESSURE_STATE": "target_option_flow_pressure_state",
            "TARGET_SHORT_EXPIRY_PRESSURE_OVERLAY": "target_short_expiry_pressure_overlay",
            "EVENT_PRESENCE_SCORE_BY_HORIZON": "10_event_presence_score_<horizon>",
            "EVENT_TIMING_PROXIMITY_SCORE_BY_HORIZON": "10_event_timing_proximity_score_<horizon>",
            "EVENT_INTENSITY_SCORE_BY_HORIZON": "10_event_intensity_score_<horizon>",
            "EVENT_DIRECTION_BIAS_SCORE_BY_HORIZON": "10_event_direction_bias_score_<horizon>",
            "EVENT_CONTEXT_ALIGNMENT_SCORE_BY_HORIZON": "10_event_context_alignment_score_<horizon>",
            "EVENT_UNCERTAINTY_SCORE_BY_HORIZON": "10_event_uncertainty_score_<horizon>",
            "EVENT_GAP_RISK_SCORE_BY_HORIZON": "10_event_gap_risk_score_<horizon>",
            "EVENT_REVERSAL_RISK_SCORE_BY_HORIZON": "10_event_reversal_risk_score_<horizon>",
            "EVENT_LIQUIDITY_DISRUPTION_SCORE_BY_HORIZON": "10_event_liquidity_disruption_score_<horizon>",
            "EVENT_CONTAGION_RISK_SCORE_BY_HORIZON": "10_event_contagion_risk_score_<horizon>",
            "EVENT_CONTEXT_QUALITY_SCORE_BY_HORIZON": "10_event_context_quality_score_<horizon>",
            "EVENT_MARKET_IMPACT_SCORE_BY_HORIZON": "10_event_market_impact_score_<horizon>",
            "EVENT_SECTOR_IMPACT_SCORE_BY_HORIZON": "10_event_sector_impact_score_<horizon>",
            "EVENT_INDUSTRY_IMPACT_SCORE_BY_HORIZON": "10_event_industry_impact_score_<horizon>",
            "EVENT_THEME_FACTOR_IMPACT_SCORE_BY_HORIZON": "10_event_theme_factor_impact_score_<horizon>",
            "EVENT_PEER_GROUP_IMPACT_SCORE_BY_HORIZON": "10_event_peer_group_impact_score_<horizon>",
            "EVENT_SYMBOL_IMPACT_SCORE_BY_HORIZON": "10_event_symbol_impact_score_<horizon>",
            "EVENT_MICROSTRUCTURE_IMPACT_SCORE_BY_HORIZON": "10_event_microstructure_impact_score_<horizon>",
            "EVENT_SCOPE_CONFIDENCE_SCORE_BY_HORIZON": "10_event_scope_confidence_score_<horizon>",
            "EVENT_SCOPE_ESCALATION_RISK_SCORE_BY_HORIZON": "10_event_scope_escalation_risk_score_<horizon>",
            "EVENT_TARGET_RELEVANCE_SCORE_BY_HORIZON": "10_event_target_relevance_score_<horizon>",
            "EVENT_RESPONSE_STRENGTH_SCORE_BY_HORIZON": "4_event_response_strength_score_<horizon>",
            "EVENT_RESPONSE_DIRECTION_SCORE_BY_HORIZON": "4_event_response_direction_score_<horizon>",
            "EVENT_RESPONSE_UNCERTAINTY_SCORE_BY_HORIZON": "4_event_response_uncertainty_score_<horizon>",
            "ALPHA_DIRECTION_SCORE_BY_HORIZON": "5_alpha_direction_score_<horizon>",
            "ALPHA_STRENGTH_SCORE_BY_HORIZON": "5_alpha_strength_score_<horizon>",
            "ALPHA_EXPECTED_RETURN_SCORE_BY_HORIZON": "5_expected_return_score_<horizon>",
            "ALPHA_CONFIDENCE_SCORE_BY_HORIZON": "5_alpha_confidence_score_<horizon>",
            "AFTER_COST_ALPHA_SCORE_BY_HORIZON": "5_after_cost_alpha_score_<horizon>",
            "SIGNAL_RELIABILITY_SCORE_BY_HORIZON": "5_signal_reliability_score_<horizon>",
            "PATH_QUALITY_SCORE_BY_HORIZON": "5_path_quality_score_<horizon>",
            "REVERSAL_RISK_SCORE_BY_HORIZON": "5_reversal_risk_score_<horizon>",
            "DRAWDOWN_RISK_SCORE_BY_HORIZON": "5_drawdown_risk_score_<horizon>",
            "ALPHA_TRADABILITY_SCORE_BY_HORIZON": "5_alpha_tradability_score_<horizon>",
            "POSITION_TARGET_POSITION_BIAS_SCORE_BY_HORIZON": "7_target_position_bias_score_<horizon>",
            "POSITION_TARGET_EXPOSURE_SCORE_BY_HORIZON": "7_target_exposure_score_<horizon>",
            "CURRENT_POSITION_ALIGNMENT_SCORE_BY_HORIZON": "7_current_position_alignment_score_<horizon>",
            "POSITION_GAP_SCORE_BY_HORIZON": "7_position_gap_score_<horizon>",
            "POSITION_GAP_MAGNITUDE_SCORE_BY_HORIZON": "7_position_gap_magnitude_score_<horizon>",
            "EXPECTED_POSITION_UTILITY_SCORE_BY_HORIZON": "7_expected_position_utility_score_<horizon>",
            "COST_TO_ADJUST_POSITION_SCORE_BY_HORIZON": "7_cost_to_adjust_position_score_<horizon>",
            "RISK_BUDGET_FIT_SCORE_BY_HORIZON": "7_risk_budget_fit_score_<horizon>",
            "POSITION_STATE_STABILITY_SCORE_BY_HORIZON": "7_position_state_stability_score_<horizon>",
            "POSITION_PROJECTION_CONFIDENCE_SCORE_BY_HORIZON": "7_projection_confidence_score_<horizon>",
            "UNDERLYING_TRADE_ELIGIBILITY_SCORE_BY_HORIZON": "8_underlying_trade_eligibility_score_<horizon>",
            "UNDERLYING_ACTION_DIRECTION_SCORE_BY_HORIZON": "8_underlying_action_direction_score_<horizon>",
            "UNDERLYING_TRADE_INTENSITY_SCORE_BY_HORIZON": "8_underlying_trade_intensity_score_<horizon>",
            "UNDERLYING_ENTRY_QUALITY_SCORE_BY_HORIZON": "8_underlying_entry_quality_score_<horizon>",
            "UNDERLYING_EXPECTED_RETURN_SCORE_BY_HORIZON": "8_underlying_expected_return_score_<horizon>",
            "UNDERLYING_ADVERSE_RISK_SCORE_BY_HORIZON": "8_underlying_adverse_risk_score_<horizon>",
            "UNDERLYING_REWARD_RISK_SCORE_BY_HORIZON": "8_underlying_reward_risk_score_<horizon>",
            "UNDERLYING_LIQUIDITY_FIT_SCORE_BY_HORIZON": "8_underlying_liquidity_fit_score_<horizon>",
            "UNDERLYING_HOLDING_TIME_FIT_SCORE_BY_HORIZON": "8_underlying_holding_time_fit_score_<horizon>",
            "UNDERLYING_ACTION_CONFIDENCE_SCORE_BY_HORIZON": "8_underlying_action_confidence_score_<horizon>",
            "OPTION_EXPRESSION_ELIGIBILITY_SCORE_BY_HORIZON": "5_option_expression_eligibility_score_<horizon>",
            "OPTION_EXPRESSION_DIRECTION_SCORE_BY_HORIZON": "5_option_expression_direction_score_<horizon>",
            "OPTION_CONTRACT_FIT_SCORE_BY_HORIZON": "5_option_contract_fit_score_<horizon>",
            "OPTION_LIQUIDITY_FIT_SCORE_BY_HORIZON": "5_option_liquidity_fit_score_<horizon>",
            "OPTION_IV_FIT_SCORE_BY_HORIZON": "5_option_iv_fit_score_<horizon>",
            "OPTION_GREEK_FIT_SCORE_BY_HORIZON": "5_option_greek_fit_score_<horizon>",
            "OPTION_REWARD_RISK_SCORE_BY_HORIZON": "5_option_reward_risk_score_<horizon>",
            "OPTION_THETA_RISK_SCORE_BY_HORIZON": "5_option_theta_risk_score_<horizon>",
            "OPTION_FILL_QUALITY_SCORE_BY_HORIZON": "5_option_fill_quality_score_<horizon>",
            "OPTION_EXPRESSION_CONFIDENCE_SCORE_BY_HORIZON": "5_option_expression_confidence_score_<horizon>",
        }
        self.assertEqual(state_vector_values.keys(), expected_state_vector_values.keys())
        for key, payload in expected_state_vector_values.items():
            self.assertEqual(state_vector_values[key]["payload"], payload)
            self.assertNotIn(key, by_key)

        for diagnostic_or_routing_key in {
            "MARKET_COVERAGE_SCORE",
            "MARKET_DATA_QUALITY_SCORE",
            "SECTOR_COVERAGE_SCORE",
            "SECTOR_DATA_QUALITY_SCORE",
            "SECTOR_EVIDENCE_COUNT",
            "SECTOR_HANDOFF_STATE",
            "SECTOR_HANDOFF_BIAS",
            "SECTOR_HANDOFF_RANK",
            "SECTOR_HANDOFF_REASON_CODES",
            "SECTOR_ELIGIBILITY_STATE",
            "SECTOR_ELIGIBILITY_REASON_CODES",
            "SECTOR_STATE_QUALITY_SCORE",
            "TARGET_STATE_QUALITY_SCORE",
            "TARGET_STATE_EVIDENCE_COUNT",
            "STATE_QUALITY_DIAGNOSTICS",
            "TARGET_STATE_EMBEDDING",
            "STATE_CLUSTER_ID",
            "MARKET_STATE_FEATURES",
            "SECTOR_STATE_FEATURES",
            "TARGET_STATE_FEATURES",
            "CROSS_STATE_FEATURES",
            "STATE_OBSERVATION_WINDOWS",
            "STATE_WINDOW_SYNC_POLICY",
            "FEATURE_QUALITY_DIAGNOSTICS",
            "TARGET_STATE_UNRESOLVED_IMPLIED_RANGE_IDENTIFIER",
            "TARGET_STATE_UNRESOLVED_STRESS_COST_IDENTIFIER",
            "TARGET_STATE_UNRESOLVED_OPTIONABILITY_COST_IDENTIFIER",
            "EVENT_DOMINANT_IMPACT_SCOPE_BY_HORIZON",
            "POSITION_PROJECTION_HANDOFF_SUMMARY_FIELD_FAMILIES",
            "POSITION_PROJECTION_DIAGNOSTIC_FIELD_FAMILIES",
        }:
            self.assertNotIn(diagnostic_or_routing_key, state_vector_values)

        for deleted_key in {
            "OPEN_PRICE",
            "HIGH_PRICE",
            "LOW_PRICE",
            "CLOSE_PRICE",
            "VOLUME",
            "VWAP",
            "TRADE_COUNT",
            "DATA_TIMEFRAME",
            "BAR_COUNT",
            "TRADE_OPEN",
            "TRADE_HIGH",
            "TRADE_LOW",
            "TRADE_CLOSE",
            "TRADE_VOLUME",
            "TRADE_VWAP",
        }:
            self.assertNotIn(deleted_key, by_key)

    def test_classification_fields_are_separate_semantic_axes(self):
        expected_classification_keys = {
            "EVENT_CATEGORY_TYPE",
            "EVENT_DEDUP_STATUS",
            "EXPOSURE_TYPE",
            "INFORMATION_ROLE_TYPE",
            "OPTION_RIGHT_TYPE",
            "REFERENCE_TYPE",
            "REGISTRY_ITEM_ARTIFACT_SYNC_POLICY_TYPE",
            "REGISTRY_ITEM_KIND",
            "SCOPE_TYPE",
            "SECTOR_TYPE",
            "SNAPSHOT_TYPE",
            "UNIVERSE_TYPE",
            "MODEL_LAYER",
        }
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in expected_classification_keys:
            self.assertEqual(rows[key]["kind"], "classification_field")
            self.assertEqual(rows[key]["payload_format"], "field_name")
            if key == "MODEL_LAYER":
                self.assertIn("explicitly assigns", rows[key]["note"])
            else:
                self.assertIn("stable lowercase token", rows[key]["note"])
        self.assertNotIn("GDELT_IMPACT_SCOPE_HINT", rows)
        self.assertNotIn("OPTION_EVENT_DETAIL_SIDE_HINT", rows)
        self.assertNotIn("TRADING_ECONOMICS_CATEGORY", rows)
        self.assertNotIn("EVENT_IMPACT_SCOPE", rows)
        self.assertNotIn("TRADE_SIDE_TYPE", rows)
        self.assertNotIn("SOURCE_EVENT_TYPE", rows)
        self.assertEqual(rows["OPTION_RIGHT_TYPE"]["payload"], "option_right_type")
        vague_payloads = {"category", "type", "status", "right", "themes", "tags", "scope", "class", "outcome", "readiness"}
        classification_payloads = {
            row["payload"] for row in rows.values() if row["kind"] == "classification_field"
        }
        self.assertFalse(classification_payloads & vague_payloads)
        for row in rows.values():
            if row["kind"] == "classification_field" and row["payload"] not in {"data_kind", "kind"}:
                self.assertRegex(row["payload"], r"_(type|status|scope|policy_type|tags|class|layer)$")
        self.assertNotIn("OPTION_RIGHT", rows)
        self.assertNotIn("STATUS", rows)
        self.assertNotIn("DATA_KIND_TEMPLATE_STATUS", rows)
        self.assertEqual(rows["REGISTRY_ITEM_ARTIFACT_SYNC_POLICY_TYPE"]["payload"], "artifact_sync_policy_type")
        self.assertNotIn("ACCEPTANCE_OUTCOME", rows)
        self.assertNotIn("REVIEW_READINESS", rows)
        self.assertNotIn("REGISTRY_ITEM_ARTIFACT_SYNC_POLICY", rows)
        self.assertEqual(rows["TITLE"]["kind"], "identity_field")
        self.assertNotIn("RETURN_ZSCORE", rows)

    def test_identity_fields_are_separate_from_plain_fields(self):
        expected_identity_keys = {
            "ID",
            "SYMBOL",
            "TITLE",
            "EVENT_ID",
            "ETF_SYMBOL",
            "ETF_HOLDING_SYMBOL",
            "ETF_HOLDING_NAME",
            "ISSUER_NAME",
            "OPTION_SYMBOL",
            "EVENT_CANONICAL_EVENT_ID",
            "EVENT_COVERED_BY_EVENT_ID",
        }
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in expected_identity_keys:
            self.assertEqual(rows[key]["kind"], "identity_field")
            self.assertIn(rows[key]["payload_format"], {"field_name", "text"})
            self.assertIn("Identity value", rows[key]["note"])
        for vague_key in {"ISSUER", "OPTION_EVENT_DETAIL_PROVIDER", "OPTION_EVENT_DETAIL_STANDARD_SOURCE"}:
            self.assertNotIn(vague_key, rows)
        self.assertEqual(rows["ISSUER_NAME"]["payload"], "issuer_name")
        self.assertNotIn("OPTION_EVENT_DETAIL_SOURCE_PROVIDER_NAME", rows)
        self.assertNotIn("TIMELINE_HEADLINE", rows)

    def test_path_fields_are_separate_from_identity_fields(self):
        expected_path_keys = {
            "REGISTRY_ITEM_PATH",
            "EVENT_REFERENCE",
        }
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in expected_path_keys:
            self.assertEqual(rows[key]["kind"], "path_field")
            self.assertIn("Path value", rows[key]["note"])
        self.assertNotIn("URL", rows)
        self.assertNotIn("EVENT_SOURCE_REF", rows)
        self.assertNotIn("EVENT_LINK_URL", rows)
        self.assertNotIn("EVENT_ANALYSIS_REPORT_URL", rows)
        self.assertNotIn("EVENT_REPORT_URL", rows)
        self.assertNotIn("EVENT_REPORT_JSON_URL", rows)
        self.assertNotIn("EVENT_SOURCE_REFERENCE", rows)
        self.assertNotIn("SOURCE_REFERENCES", rows)
        self.assertEqual(rows["EVENT_REFERENCE"]["payload"], "reference")
        self.assertNotIn("TRADING_ECONOMICS_REFERENCE_PERIOD", rows)

    def test_text_fields_are_separate_from_plain_fields(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in {
            "REGISTRY_ITEM_NOTE",
            "SUMMARY",
            "EVENT_COVERAGE_REASON",
        }:
            self.assertEqual(rows[key]["kind"], "text_field")
            self.assertIn("Text value", rows[key]["note"])

    def test_parameter_fields_are_separate_from_text_and_plain_fields(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertNotIn("DATA_TASK_PARAMS", rows)

    def test_registered_artifact_sync_policies_match_sql_constraint(self):
        schema = Path("scripts/registry/sql/trading_registry.sql").read_text()
        constraint = re.search(
            r"CONSTRAINT trading_registry_artifact_sync_policy_check\s+CHECK \(.*?OR artifact_sync_policy IN \((.*?)\)\s+\);",
            schema,
            re.S,
        ).group(1)
        constrained_policies = tuple(re.findall(r"'([^']+)'", constraint))

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registered_policies = tuple(
                row["payload"]
                for row in csv.DictReader(csv_file)
                if row["kind"] == "status_value"
                and row["applies_to"] == "artifact_sync_policy_type"
            )

        self.assertEqual(sorted(registered_policies), sorted(constrained_policies))
        self.assertIn("registry_only", registered_policies)
        self.assertIn("sync_artifact", registered_policies)
        self.assertIn("review_on_merge", registered_policies)

    def test_test_scripts_are_documented_and_not_registered_as_scripts(self):
        test_scripts = sorted(Path("tests").glob("test_*.py"))
        self.assertTrue(test_scripts)

        tests_readme = Path("tests/README.md").read_text()
        for script in test_scripts:
            self.assertIn(f"`{script.name}`", tests_readme)

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            script_rows = [row for row in csv.DictReader(csv_file) if row["kind"] == "script"]

        for row in script_rows:
            normalized_path = (row["path"] or "").replace("\\", "/")
            self.assertNotIn("/tests/", normalized_path)
            self.assertFalse(Path(normalized_path).name.startswith("test_"), row["key"])

    def test_map_registry_item_row(self):
        item = map_registry_item_row(create_row(payload_format="field_name"))
        self.assertEqual(item.id, "fld_A7K3P2Q9")
        self.assertEqual(item.payload_format, "field_name")
        self.assertEqual(item.applies_to, "trading_registry")
        self.assertEqual(item.artifact_sync_policy, "sync_artifact")
        self.assertIsNone(item.path)

    def test_id_only_registry_helpers_return_key_payload_and_path(self):
        calls = []

        def query(sql, params):
            calls.append((sql, params))
            if params[0] == "missing":
                return {"rows": []}
            return {
                "rows": [
                    create_row(
                        id="rep_H6S3V8LA",
                        kind="repo",
                        key="TRADING_MANAGER_REPO",
                        payload_format="repo_name",
                        payload="trading-manager",
                        path="/root/projects/trading-manager",
                        applies_to=None,
                    )
                ]
            }

        reader = RegistryReader(query)
        self.assertEqual(reader.get_key_by_id("rep_H6S3V8LA"), "TRADING_MANAGER_REPO")
        self.assertEqual(reader.get_payload_by_id("rep_H6S3V8LA"), "trading-manager")
        self.assertEqual(reader.get_path_by_id("rep_H6S3V8LA"), "/root/projects/trading-manager")
        self.assertIsNone(reader.get_key_by_id("missing"))
        self.assertIsNone(reader.get_payload_by_id("missing"))
        self.assertIsNone(reader.get_path_by_id("missing"))
        self.assertTrue(all("WHERE id = %s" in sql for sql, _ in calls))

    def test_manager_registry_value_helpers_resolve_by_stable_id(self):
        self.assertEqual(registry_payload("trm_MRM001"), "market_regime_model")
        self.assertEqual(registry_payload("trm_L2CES001"), "context_etf_state")
        self.assertEqual(registry_payload("trm_L2XES001"), "cross_etf_summary")
        self.assertEqual(registry_payload("trm_L2TCP001"), "target_context_profile")
        self.assertEqual(registry_payload("trm_M6DRP01"), "model_06_dynamic_risk_policy")
        self.assertEqual(registry_payload("mlv_L10ERG001"), "layer_10_event_risk_governor")
        self.assertTrue(registry_value("out_TL2CTX001", "path").endswith("layer_02_target_context_mapping.csv"))

    def test_require_item_by_id_throws_for_missing_item(self):
        reader = RegistryReader(lambda _sql, _params: {"rows": []})
        with self.assertRaisesRegex(KeyError, "Registry item not found for id: fld_missing"):
            reader.require_item_by_id("fld_missing")

    def test_id_lookup_rejects_blank_id_inputs(self):
        reader = RegistryReader(lambda _sql, _params: {"rows": []})
        with self.assertRaisesRegex(TypeError, "id must be a non-empty string"):
            reader.get_key_by_id("   ")

    def test_list_items_by_kind_filters_by_kind(self):
        def query(sql, params):
            self.assertIn("WHERE kind = %s", sql)
            self.assertIn("ORDER BY key ASC", sql)
            self.assertEqual(params, ["repo"])
            return [create_row(kind="repo", key="TRADING_MANAGER_REPO", payload="trading-manager")]

        reader = RegistryReader(query)
        items = reader.list_items_by_kind("repo")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].kind, "repo")
        with self.assertRaisesRegex(TypeError, "kind must be a non-empty string"):
            reader.list_items_by_kind("   ")

    def test_parse_registry_rejects_invalid_json_and_returns_objects(self):
        with self.assertRaisesRegex(ValueError, "is not valid JSON"):
            parse_registry("{", "/root/secrets/registry.json")
        parsed = parse_registry(
            json.dumps({"example-service": {"path": "/root/secrets/example-service.json"}}),
            "/root/secrets/registry.json",
        )
        self.assertEqual(parsed["example-service"]["path"], "/root/secrets/example-service.json")

    def test_get_secret_entry_from_registry_resolves_source_json_aliases(self):
        entry = get_secret_entry_from_registry(
            {
                "github": {
                    "path": "/root/secrets/github.json",
                    "kind": "source_secret_file",
                    "use": "git operations",
                    "fields": {"pat": "GitHub personal access token"},
                }
            },
            "github",
            "/root/secrets/registry.json",
        )
        self.assertEqual(entry["alias"], "github")
        self.assertEqual(entry["path"], "/root/secrets/github.json")
        self.assertEqual(entry["kind"], "source_secret_file")

    def test_secret_resolver_loads_source_json_field_text_by_config_id(self):
        reads = []

        def query(sql, params):
            self.assertIn("WHERE id = %s", sql)
            self.assertEqual(params, ["cfg_EXAMPLESECRET"])
            return {
                "rows": [
                    create_row(
                        id="cfg_EXAMPLESECRET",
                        kind="config",
                        key="EXAMPLE_SERVICE_SECRET_ALIAS",
                        payload_format="secret_alias",
                        payload="example-service",
                        path="/root/secrets/example-service.json",
                        applies_to=None,
                    )
                ]
            }

        def read_text(path):
            reads.append(path)
            if path == "/root/secrets/registry.json":
                return json.dumps(
                    {
                        "example-service": {
                            "path": "/root/secrets/example-service.json",
                            "kind": "source_secret_file",
                            "use": "example service credentials",
                            "fields": {
                                "allowed_ip_address": "example allowlisted IPv4 address",
                                "api_key": "example service API key",
                                "endpoint": "example service API endpoint",
                            },
                        }
                    }
                )
            if path == "/root/secrets/example-service.json":
                return json.dumps(
                    {
                        "allowed_ip_address": "203.0.113.10",
                        "api_key": "secret-value",
                        "endpoint": "https://example.test/v1",
                        "secret_key": "other-secret",
                    }
                )
            raise AssertionError(f"unexpected read: {path}")

        resolver = SecretResolver(query, registry_path="/root/secrets/registry.json", read_text=read_text)
        raw_secret_json = resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET")
        self.assertEqual(json.loads(raw_secret_json)["api_key"], "secret-value")
        self.assertEqual(
            resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET", "api_key"),
            "secret-value",
        )
        self.assertEqual(
            resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET", "allowed_ip_address"),
            "203.0.113.10",
        )
        self.assertEqual(
            resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET", "endpoint"),
            "https://example.test/v1",
        )
        with self.assertRaisesRegex(KeyError, "Secret JSON field not found"):
            resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET", "missing")
        self.assertEqual(reads[0], "/root/secrets/registry.json")

    def test_secret_resolver_rejects_non_config_items(self):
        resolver = SecretResolver(
            lambda _sql, _params: {"rows": [create_row(kind="term", payload="Project sentinel")]},
            read_text=lambda _path: "{}",
        )
        with self.assertRaisesRegex(ValueError, "must be kind=config"):
            resolver.load_secret_text_by_config_id("trm_OPENCLAW")


    def test_realtime_forward_validation_policy_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertIn("REALTIME_FORWARD_VALIDATION_POLICY", rows)
        self.assertIn("supplements_not_replaces_initial_historical_splits", rows["REALTIME_FORWARD_VALIDATION_POLICY"]["payload"])
        self.assertIn("append_only_point_in_time_capture_required", rows["REALTIME_FORWARD_VALIDATION_POLICY"]["payload"])
        self.assertIn("frozen_model_config_refs_required", rows["REALTIME_FORWARD_VALIDATION_POLICY"]["payload"])
        self.assertEqual(rows["REALTIME_FORWARD_VALIDATION_DATASET"]["payload"], "realtime_forward_validation_dataset")
        self.assertIn("model_dataset_snapshot", rows["REALTIME_FORWARD_VALIDATION_DATASET"]["applies_to"])
        self.assertIn("report_historical_live_route_simulation", rows["MODEL_VALIDATION_EVIDENCE_VIEW_POLICY"]["payload"])
        self.assertIn("report_realtime_shadow_forward_after_label_maturity", rows["MODEL_VALIDATION_EVIDENCE_VIEW_POLICY"]["payload"])
        self.assertIn("does_not_authorize_provider_streams_or_broker_mutation", rows["EXECUTION_REALTIME_CAPTURE_FOR_VALIDATION_BOUNDARY"]["payload"])


    def test_execution_realtime_coverage_contracts_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(
            rows["EXECUTION_REALTIME_INPUT_COVERAGE_MATRIX"]["payload"],
            "execution_realtime_input_coverage",
        )
        realtime_coverage = rows["EXECUTION_REALTIME_INPUT_COVERAGE_MATRIX"]["applies_to"]
        for model_id in (
            "model_01_market_regime",
            "model_02_sector_context",
            "model_03_target_state_vector",
            "model_04_event_failure_risk",
            "model_05_alpha_confidence",
            "model_06_dynamic_risk_policy",
            "model_07_position_projection",
            "model_08_underlying_action",
            "model_09_option_expression",
            "model_10_event_risk_governor",
        ):
            self.assertIn(model_id, realtime_coverage)
        self.assertEqual(rows["REALTIME_CAPTURE_CONTRACT"]["payload"], "realtime_capture_contract")
        self.assertIn("forward_holdout", rows["REALTIME_CAPTURE_CONTRACT"]["applies_to"])
        self.assertIn("ready_signal", rows["REALTIME_CAPTURE_CONTRACT"]["applies_to"])
        self.assertIn("zero_provider_calls", rows["EXECUTION_REALTIME_COVERAGE_GAP_POLICY"]["payload"])
        self.assertIn("layer_07_broker_account_route_deferred", rows["EXECUTION_REALTIME_LAYER_GAP_SUMMARY"]["payload"])
        self.assertIn("layer_09_thetadata_terminal_required", rows["EXECUTION_REALTIME_LAYER_GAP_SUMMARY"]["payload"])


    def test_execution_realtime_adapter_scaffold_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(
            rows["EXECUTION_REALTIME_SUBSCRIPTION_PLAN"]["payload"],
            "execution_realtime_subscription_plan",
        )
        self.assertIn("no_provider_calls", rows["EXECUTION_REALTIME_SUBSCRIPTION_PLAN"]["applies_to"])
        self.assertEqual(
            rows["EXECUTION_REALTIME_SUBSCRIPTION_PLAN_SET"]["payload"],
            "execution_realtime_subscription_plan_set",
        )
        self.assertEqual(rows["REALTIME_CAPTURE_VALIDATION"]["payload"], "realtime_capture_validation")
        self.assertIn("no_model_activation", rows["REALTIME_CAPTURE_VALIDATION"]["applies_to"])
        self.assertIn("plan_realtime_capture.py", rows["EXECUTION_REALTIME_CAPTURE_PLAN"]["path"])
        self.assertIn("validate_realtime_capture.py", rows["EXECUTION_REALTIME_CAPTURE_VALIDATE"]["path"])
        self.assertIn("live_observe_requires_live_stream_approval_ref", rows["EXECUTION_REALTIME_LIVE_OBSERVE_GATE_POLICY"]["payload"])

    def test_realtime_feature_decision_handoff_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["REALTIME_FEATURE_SNAPSHOT"]["payload"], "realtime_feature_snapshot")
        self.assertIn("historical_feature_parity", rows["REALTIME_FEATURE_SNAPSHOT"]["applies_to"])
        self.assertEqual(
            rows["EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT"]["payload"],
            "execution_model_decision_input_snapshot",
        )
        self.assertIn("historical_model_decision_handoff", rows["EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT"]["applies_to"])
        self.assertIn("current_model_component_route", rows["EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT"]["applies_to"])
        self.assertNotIn("layers_1_10", rows["EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT"]["applies_to"])
        self.assertEqual(
            rows["EXECUTION_MODEL_DECISION_COMPONENT_INPUT"]["payload"],
            "execution_model_decision_component_input",
        )
        self.assertIn("runtime_component", rows["EXECUTION_MODEL_DECISION_COMPONENT_INPUT"]["applies_to"])
        self.assertEqual(
            rows["EXECUTION_MODEL_DECISION_INPUT_VALIDATION"]["payload"],
            "execution_model_decision_input_validation",
        )
        self.assertIn("current_model_component_route", rows["EXECUTION_MODEL_DECISION_INPUT_VALIDATION"]["applies_to"])
        self.assertIn("build_realtime_feature_snapshot.py", rows["EXECUTION_REALTIME_FEATURE_SNAPSHOT_BUILD"]["path"])
        self.assertIn("build_realtime_model_input.py", rows["EXECUTION_REALTIME_MODEL_INPUT_BUILD"]["path"])
        self.assertIn("validate_realtime_model_input.py", rows["EXECUTION_REALTIME_MODEL_INPUT_VALIDATE"]["path"])
        self.assertIn("historical_feature_parity_required", rows["EXECUTION_REALTIME_MODEL_DECISION_HANDOFF_POLICY"]["payload"])
        self.assertIn("runtime_component_refs_required", rows["EXECUTION_REALTIME_MODEL_DECISION_HANDOFF_POLICY"]["payload"])
        self.assertIn("placeholder_context_refs_use_placeholder_upstream_context_scheme", rows["EXECUTION_REALTIME_PLACEHOLDER_CONTEXT_REF_POLICY"]["payload"])
        self.assertEqual(
            rows["EXECUTION_MODEL_DECISION_INPUT_READY_FOR_HISTORICAL_MODEL_DECISION_INPUT"]["payload"],
            "ready_for_historical_model_decision_input",
        )

    def test_model_realtime_decision_handoff_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(
            rows["MODEL_REALTIME_DECISION_INPUT_VALIDATION"]["payload"],
            "model_realtime_decision_input_validation",
        )
        self.assertIn("execution_model_decision_input_snapshot", rows["MODEL_REALTIME_DECISION_INPUT_VALIDATION"]["applies_to"])
        self.assertEqual(
            rows["MODEL_REALTIME_DECISION_ROUTE_PLAN"]["payload"],
            "model_realtime_decision_route_plan",
        )
        self.assertIn("current_model_component_route", rows["MODEL_REALTIME_DECISION_ROUTE_PLAN"]["applies_to"])
        self.assertIn("execution unit is component", rows["MODEL_REALTIME_DECISION_ROUTE_PLAN"]["note"])
        self.assertNotIn("layers_1_10", rows["MODEL_REALTIME_DECISION_ROUTE_PLAN"]["applies_to"])
        self.assertEqual(
            rows["MODEL_REALTIME_DECISION_COMPONENT_ROUTE"]["payload"],
            "model_realtime_decision_component_route",
        )
        self.assertIn("runtime_component", rows["MODEL_REALTIME_DECISION_COMPONENT_ROUTE"]["applies_to"])
        self.assertEqual(
            rows["MODEL_REALTIME_DECISION_ROUTE_PLAN_VALIDATION"]["payload"],
            "model_realtime_decision_route_plan_validation",
        )
        self.assertIn(
            "component_01_intake",
            rows["MODEL_REALTIME_DECISION_COMPONENT_ORDER"]["payload"],
        )
        self.assertIn(
            "component_06_execution_gate",
            rows["MODEL_REALTIME_DECISION_REQUIRED_COMPONENTS"]["payload"],
        )
        self.assertEqual(
            rows["MODEL_REALTIME_DECISION_OPTIONAL_COMPONENTS"]["payload"],
            "component_04_expression_review;component_07_failure_review",
        )
        self.assertIn("plan_realtime_decision_handoff.py", rows["MODEL_REALTIME_DECISION_HANDOFF_PLAN"]["path"])
        self.assertIn("validate_realtime_decision_handoff.py", rows["MODEL_REALTIME_DECISION_HANDOFF_VALIDATE"]["path"])
        self.assertIn("no_production_model_activation", rows["MODEL_REALTIME_DECISION_HANDOFF_POLICY"]["payload"])
        self.assertIn("component_route_coverage_required", rows["MODEL_REALTIME_DECISION_HANDOFF_POLICY"]["payload"])
        self.assertIn("route_plan_id_prefix=rtdroute_", rows["MODEL_REALTIME_DECISION_ROUTE_PLAN_ID_POLICY"]["payload"])
        self.assertEqual(
            rows["MODEL_REALTIME_DECISION_COMPONENT_ROUTE_READY_FOR_FIXTURE_SHADOW_GENERATION"]["payload"],
            "ready_for_fixture_shadow_generation",
        )
        self.assertEqual(
            rows["MODEL_REALTIME_DECISION_ROUTE_PLAN_READY_FOR_FIXTURE_SHADOW_RUNTIME_COMPONENT_ROUTE"]["payload"],
            "ready_for_fixture_shadow_runtime_component_route",
        )
        self.assertEqual(
            rows["MODEL_REALTIME_DECISION_COMPONENT_ROUTE_BLOCKED_INPUT_VALIDATION_FAILED"]["payload"],
            "blocked_input_validation_failed",
        )
        self.assertEqual(
            rows["MODEL_REALTIME_DECISION_ROUTE_PLAN_BLOCKED_REALTIME_DECISION_INPUT_VALIDATION"]["payload"],
            "blocked_realtime_decision_input_validation",
        )

    def test_manager_realtime_shadow_handoff_receipt_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(
            rows["MANAGER_REALTIME_SHADOW_HANDOFF_VALIDATION"]["payload"],
            "manager_realtime_shadow_handoff_validation",
        )
        self.assertIn("model_realtime_decision_route_plan", rows["MANAGER_REALTIME_SHADOW_HANDOFF_VALIDATION"]["applies_to"])
        self.assertIn("current_model_component_route", rows["MANAGER_REALTIME_SHADOW_HANDOFF_VALIDATION"]["applies_to"])
        self.assertEqual(
            rows["MANAGER_REALTIME_SHADOW_HANDOFF_RECEIPT"]["payload"],
            "manager_realtime_shadow_handoff_receipt",
        )
        self.assertIn("ready_signal", rows["MANAGER_REALTIME_SHADOW_HANDOFF_RECEIPT"]["applies_to"])
        self.assertEqual(
            rows["MANAGER_REALTIME_SHADOW_HANDOFF_CONTROL_PLANE_BUNDLE"]["payload"],
            "manager_realtime_shadow_handoff_control_plane_bundle",
        )
        self.assertIn("record_realtime_shadow_handoff.py", rows["MANAGER_REALTIME_SHADOW_HANDOFF_RECORD"]["path"])
        self.assertIn("no_model_activation", rows["MANAGER_REALTIME_SHADOW_HANDOFF_POLICY"]["payload"])
        self.assertIn("mgrreq_realtime_shadow_rehearsal", rows["MANAGER_REALTIME_SHADOW_REHEARSAL_DEFAULT_ID_POLICY"]["payload"])

    def test_execution_order_construction_gate_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["EXECUTION_ORDER_CONSTRUCTION_APPROVAL"]["payload"], "execution_order_construction_approval")
        self.assertEqual(rows["EXECUTION_ORDER_CONSTRUCTION_APPROVAL_VALIDATION"]["payload"], "execution_order_construction_approval_validation")
        self.assertEqual(rows["EXECUTION_BROKER_ORDER_INTENT"]["payload"], "execution_broker_order_intent")
        self.assertEqual(rows["EXECUTION_BROKER_ORDER_INTENT_RESULT"]["payload"], "execution_broker_order_intent_result")
        self.assertIn("build_broker_order_intent.py", rows["EXECUTION_BROKER_ORDER_INTENT_BUILD"]["path"])
        self.assertIn("broker_submission_requires_separate_execution_gate", rows["EXECUTION_ORDER_CONSTRUCTION_POLICY"]["payload"])

    def test_realtime_formal_live_observe_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["REALTIME_LIVE_OBSERVE_APPROVAL"]["payload"], "realtime_live_observe_approval")
        self.assertEqual(rows["REALTIME_LIVE_OBSERVE_APPROVAL_VALIDATION"]["payload"], "realtime_live_observe_approval_validation")
        self.assertEqual(rows["EXECUTION_REALTIME_LIVE_OBSERVE_RESULT"]["payload"], "execution_realtime_live_observe_result")
        self.assertEqual(rows["REALTIME_LIVE_OBSERVATION"]["payload"], "realtime_live_observation")
        self.assertIn("execute_live_observe.py", rows["EXECUTION_REALTIME_LIVE_OBSERVE_EXECUTE"]["path"])
        self.assertIn("separate_execution_gate", rows["REALTIME_FORMAL_INTEGRATION_POLICY"]["payload"])
        self.assertIn("persist_completion_rows", rows["MANAGER_REALTIME_SHADOW_HANDOFF_PERSISTENCE"]["applies_to"])

    def test_realtime_live_observe_fixture_scaffold_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(
            rows["EXECUTION_REALTIME_LIVE_OBSERVE_ADAPTER_PLAN"]["payload"],
            "execution_realtime_live_observe_adapter_plan",
        )
        self.assertEqual(
            rows["EXECUTION_REALTIME_LIVE_OBSERVE_ADAPTER_PLAN_SCRIPT"]["payload"],
            "PYTHONPATH=src python3 scripts/execution/plan_live_observe_adapters.py --mode fixture_replay --instrument-ref ${INSTRUMENT_REF}",
        )
        self.assertEqual(
            rows["EXECUTION_REALTIME_CAPTURE_FIXTURE_SET"]["payload"],
            "execution_realtime_capture_fixture_set",
        )
        self.assertEqual(
            rows["EXECUTION_REALTIME_SHADOW_FIXTURE_BUNDLE"]["payload"],
            "execution_realtime_shadow_fixture_bundle",
        )
        self.assertEqual(
            rows["MANAGER_REALTIME_SHADOW_HANDOFF_REHEARSAL"]["payload"],
            "manager_realtime_shadow_handoff_rehearsal",
        )
        self.assertIn("rehearse_realtime_shadow_handoff.py", rows["MANAGER_REALTIME_SHADOW_HANDOFF_REHEARSE"]["path"])
        self.assertIn("live_observe_requires_reviewed_live_stream_approval_ref", rows["REALTIME_LIVE_OBSERVE_FIXTURE_POLICY"]["payload"])


if __name__ == "__main__":
    unittest.main()

class WebSearchHelperTests(unittest.TestCase):
    def test_csv_registry_query_resolves_config_secret(self):
        from trading_registry import SecretResolver, create_csv_registry_query

        rows = {
            "id": "cfg_TESTSEARCH",
            "kind": "config",
            "key": "TEST_SEARCH_SECRET_ALIAS",
            "payload_format": "secret_alias",
            "payload": "test-search",
            "path": "/root/secrets/test-search.json",
            "applies_to": "unit",
            "artifact_sync_policy": "registry_only",
            "note": "unit",
            "created_at": "",
            "updated_at": "",
        }

        def read_text(path: str) -> str:
            if path.endswith("registry.csv"):
                raise AssertionError("registry CSV should be read by query helper")
            if path == "/root/secrets/registry.json":
                return json.dumps({"test-search": {"path": "/root/secrets/test-search.json"}})
            if path == "/root/secrets/test-search.json":
                return json.dumps({"api_key": "search-key"})
            raise AssertionError(path)

        import csv as _csv
        import tempfile as _tempfile

        with _tempfile.TemporaryDirectory() as temp_dir:
            registry_csv = Path(temp_dir) / "registry.csv"
            with registry_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = _csv.DictWriter(handle, fieldnames=list(rows))
                writer.writeheader()
                writer.writerow(rows)
            resolver = SecretResolver(create_csv_registry_query(registry_csv), read_text=read_text)
            self.assertEqual(resolver.load_secret_text_by_config_id("cfg_TESTSEARCH", "api_key"), "search-key")

    def test_bigquery_client_normalizes_query_results_with_mock_transport(self):
        from trading_bigquery.client import BigQueryClient
        from unittest.mock import patch

        class FakeResponse:
            status = 200

            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps(self.payload).encode()

        service_account = {
            "type": "service_account",
            "project_id": "unit-project",
            "client_email": "unit@example.test",
            "token_uri": "https://oauth.example.test/token",
            "private_key": "-----BEGIN PRIVATE KEY-----\nunit\n-----END PRIVATE KEY-----\n",
        }
        query_payload = {"schema": {"fields": [{"name": "url"}, {"name": "title"}]}, "rows": [{"f": [{"v": "https://example.test"}, {"v": "Example"}]}], "totalRows": "1"}

        with patch("trading_bigquery.client._jwt_encode_rs256", return_value="signed.jwt"), patch("urllib.request.urlopen", side_effect=[FakeResponse({"access_token": "token", "expires_in": 3600}), FakeResponse(query_payload)]) as urlopen:
            result = BigQueryClient(service_account).query("SELECT url, title", max_results=1)

        self.assertEqual(result.schema, ["url", "title"])
        self.assertEqual(result.rows[0]["title"], "Example")
        token_request = urlopen.call_args_list[0].args[0]
        query_request = urlopen.call_args_list[1].args[0]
        self.assertEqual(token_request.full_url, "https://oauth.example.test/token")
        self.assertEqual(query_request.headers["Authorization"], "Bearer token")
        self.assertIn("/projects/unit-project/queries", query_request.full_url)

    def test_brave_search_client_normalizes_results_with_mock_transport(self):
        from trading_web_search.brave import BraveSearchClient
        from unittest.mock import patch
        import io

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({"web": {"results": [{"title": "A", "url": "https://example.test", "description": "D", "site_name": "example"}]}}).encode()

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            results = BraveSearchClient("unit-key").search("macro release calendar", count=1)
        self.assertEqual(results[0].title, "A")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers["X-subscription-token"], "unit-key")
        self.assertIn("macro+release+calendar", request.full_url)
