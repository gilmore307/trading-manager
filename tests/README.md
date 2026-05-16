# Tests

`tests/` owns first-party tests for the `trading-manager` source packages and repository governance checks.

## Boundary

- Test scripts are repository-local verification assets, not registry entries.
- Do not register test files as registry `script` rows.
- Every first-party `test_*.py` script in this directory must be listed in the inventory below with what it verifies.
- Update this README whenever a test script is added, renamed, split, merged, or removed.

## Inventory

- `test_agent_error_handler.py` verifies:
  - server-wide `server_error_agent_request` construction from command/log/evidence refs;
  - centralized safety boundaries for diagnosis and repair;
  - queued diagnosis artifact behavior when no reviewed runner is configured;
  - explicit configured-runner invocation behavior for safe local test runners.
  - Discord alert command construction through OpenClaw message CLI using the reviewed channel target.
  - monotonic owner-facing error numbering, duplicate suppression, and append-only catalog behavior.
  - safe auto-repair runner behavior for scheduler dead-PID lock files.

- `test_dataset_evidence.py` verifies:
  - manager-visible dataset evidence collection from model governance rows;
  - split-role normalization and chronological month coverage;
  - collected evidence feeding dataset expansion decisions;
  - promotion metric failures surfacing forward-holdout gaps.

- `test_dataset_expansion.py` verifies:
  - manager-owned dataset expansion role selection across train, calibration, validation, test, and forward holdout;
  - upstream dependency ordering before downstream layer expansion;
  - safe Layer 1 task-key preparation with zero provider calls, model activation, or broker execution.

- `test_information_pass.py` verifies:
  - `manager_controlled_information_pass` report construction;
  - safe 2016-01 information-pass writes with zero provider calls, model activation, broker execution, or storage lifecycle mutation;
  - optional `autonomous_historical_provider_acquisition` plan-only validation without dispatch;
  - non-stressful host resource snapshot collection.

- `test_model_training_workflow.py` verifies:
  - base Layer 1-7 manager workflow graph coverage;
  - per-layer data acquisition, feature, model generation, evaluation, promotion-review, and maintenance stages;
  - Layer 1 task-key preparation to autonomous provider dispatch gate progression;
  - explicit no-dedicated-feature handling for Layers 5-7.

- `test_layer_three_target_state.py` verifies:
  - local Layer 3 target-state source materialization from completed Layer 2 feed artifacts;
  - source task-key, candidate, and merged-bar evidence generation without embedding large rows in the task key;
  - zero provider calls, model activation, or broker execution in dry-run materialization.

- `test_layer_eight_event_risk_governor.py` verifies:
  - local Layer 8 event-risk source materialization from completed Layer 2 feed artifacts;
  - detector/source task-key evidence generation for `source_04_event_overlay` without provider dispatch;
  - reviewed local news/SEC/macro feed artifact discovery and write-mode coverage blocking;
  - zero provider calls, model activation, or broker execution in dry-run materialization.

- `test_model_training_invalidation.py` verifies:
  - state-only invalidation of stale Layer 4+ workflow stages after event-source contract repair;
  - preservation of Layer 1-3 workflow stages;
  - dry-run invalidation leaves state files unchanged.

- `test_event_feed_backfill.py` verifies:
  - required Layer 8 event-feed task-key preparation for Alpaca news, GDELT news, Trading Economics calendar, and SEC company financials;
  - event-feed preparation writes task keys without provider calls, model activation, broker execution, or dashboard read-model writes.

- `test_event_feed_dispatch.py` verifies:
  - Layer 8 event-feed dispatch defaults to validation-only with zero provider calls;
  - explicit dispatch writes runtime task keys that enable only the selected event-feed provider controls.

- `test_layer_eight_option_expression.py` verifies:
  - legacy `layer_08_option_expression` gate review over completed conceptual Layer 6 / physical Layer 7 rows;
  - reviewed no-provider skip behavior when all Layer 7 rows are no-trade/maintain/neutral;
  - active Layer 7 target chains producing ThetaData/source_05 option-snapshot request previews without provider calls.

- `test_layer_eight_feature_stage.py` verifies:
  - manager-owned Layer 8 feature-stage adapter behavior;
  - first-class no-provider/no-feature skip receipt generation after a reviewed zero-active-target gate;
  - delegation to trading-data `feature_08_option_expression` with month-scoped source windows after active-path acquisition.

- `test_model_training_state.py` verifies:
  - durable `manager_model_training_workflow_state` initialization;
  - approval-ref and receipt-driven stage advancement;
  - downstream readiness after upstream stage completion;
  - not-applicable feature/source stages for Layers 5-7;
  - month-scoped checkpoint path derivation and separate `provider_calls_observed` accounting.

- `test_provider_dispatch.py` verifies:
  - Layer 1 provider-dispatch approval validation;
  - default plan-only behavior with zero provider calls;
  - concrete trading-data command planning after `autonomous_historical_provider_acquisition` validation;
  - execution requiring exact `manager_provider_dispatch_proposal_validation` evidence;
  - optional per-request failure continuation for approved batches;
  - registered accepted-failure skips with zero repeated provider calls.

- `test_failure_register.py` verifies:
  - `manager_failure_register` validation;
  - accepted-skip and corrected failures requiring agent review evidence;
  - durable skip disposition for reviewed normal historical absences.

- `test_stage_run_controller.py` verifies:
  - one-step conservative `manager_stage_run_controller_receipt` behavior;
  - automatic bounded provider-dispatch execution when the dashboard requests it;
  - hard stops at provider-execution and dry-run/no-write gates.

- `test_stage_run_dashboard.py` verifies:
  - single `manager_stage_run_dashboard` receipt construction from coverage and next provider-dispatch preview;
  - packet status discovery under the provider-dispatch plan runtime root;
  - failed stage coverage takes priority over next-packet suggestions.

- `test_stable_semantic_ids.py` verifies:
  - active code, tests, and docs use the stable `monthly_backfill` semantic id instead of reintroducing legacy version-suffixed storage names.

- `test_stage_coverage.py` verifies:
  - `manager_stage_coverage` classification from `task_summary` rows;
  - partial coverage such as `3/19` remaining blocked from downstream unlock;
  - full expected coverage allowing workflow stage completion;
  - failed coverage preventing downstream unlock.

- `test_stage_reconcile.py` verifies:
  - provider-stage receipt discovery by reviewed universe/request id;
  - completion receipt normalization without provider calls or default writes;
  - failed receipt proposal rows with `failure_status=agent_review_required`, not accepted/skip disposition;
  - optional control-plane persistence, failure-register persistence, coverage report writing, and workflow advancement from written coverage evidence.

- `test_stage_executor.py` verifies:
  - ready safe offline stage execution;
  - receipt/log creation;
  - refusal to execute Layer 1/2 provider-dispatch stages through the offline executor.

- `test_model_promotion.py` verifies:
  - unified model promotion review request planning;
  - registered model target coverage across the legacy physical model targets;
  - one shared `model_promotion_review` request kind for all model layers.

- `test_provider_dispatch.py` verifies:
  - `autonomous_historical_provider_acquisition` validation for bounded non-dry-run provider acquisition requests;
  - rejection of dry-run requests, missing provider-dispatch guard policy, wrong provider scope, over-wide windows, over-count batches, and broker-execution approval.

- `test_provider_dispatch.py` verifies:
  - skip-aware `manager_provider_dispatch_proposal` review-template planning;
  - exclusion of registered accepted skips before approval;
  - exact proposal-bound validation of reviewed `autonomous_historical_provider_acquisition` request ids, skip exclusion, and max request bounds;
  - proposal/validation outputs stay non-dispatching with zero provider calls;
  - pending-only planning excludes already ready/reviewed-terminal requests and blocks unreviewed failed stage requests.

- `test_stage_run_dashboard.py` verifies:
  - complete `manager_provider_dispatch_packet` bundle generation;
  - packet files for proposal, reviewed-approval template, editable reviewed approval, validation output, dispatch templates, reconcile templates, and status templates;
  - registered skip exclusion before packet command construction;
  - read-only packet lifecycle/status transitions from review template through validation, plan, execute, reconcile, and inconsistency detection;
  - packet rehearsal with ephemeral approval files, no persistent approval/validation/dispatch artifacts, and zero provider calls;
  - terminal stage requests are excluded before provider command construction.

- `test_historical_training.py` verifies:
  - manager-owned Layer 1 historical-training batch preparation;
  - full market-regime ETF universe request expansion;
  - task-key payload materialization and handoff validation without provider calls, model activation, or broker execution.

- `test_monthly_backfill.py` verifies:
  - monthly window generation;
  - accepted `2016-01` common start behavior;
  - OKX crypto joining later at `2018-01`;
  - current-only feeds staying out of historical backfill requests;
  - dry-run `manager_request` JSONL shape.

- `test_nasdaq_earnings_baseline.py` verifies:
  - future Nasdaq earnings EPS-baseline snapshot request planning by date;
  - `calendar_discovery` task-key preparation for trading-execution without provider calls, model activation, broker execution, or dashboard writes;
  - baseline-use controls that restrict future use to pre-event EPS forecast fields and exclude actual/surprise fields.

- `test_request_payloads.py` verifies:
  - `storage://trading-manager/...` parameter refs resolve to local storage-root paths;
  - monthly backfill requests materialize component-readable `task_key.json` payloads;
  - request-scoped `input_binding` metadata captures parameter payload refs and hashes;
  - all default `2016-01` monthly backfill feeds receive required starter params.

- `test_request_handoff.py` verifies:
  - materialized request payloads load through component `build_context` without dispatch/provider calls;
  - hash-backed `input_binding` metadata must match the local payload;
  - provider-call-enabled payloads are rejected by the dry-run handoff validator.

- `test_safe_error_repair.py` verifies:
  - reviewed deterministic safe auto-repair behavior for scheduler dead-PID lock files;
  - unknown errors remain diagnosis-only without mutation.

- `test_scheduler.py` verifies:
  - regular-trading-day-only market-hours protection;
  - weekend and market-holiday exemptions from the 09:20-16:10 ET pause window;
  - resource-pressure gating that reserves live-system capacity;
  - scheduler ready/backoff/executed decisions for safe offline Layer 1 preparation without provider dispatch.

- `test_scheduler_daemon.py` verifies:
  - `manager_scheduler_daemon_state` checkpoint round-tripping and resume-scope updates;
  - single-instance lock behavior;
  - error checkpointing for restart-safe failure visibility;
  - persistent daemon loop state/log writing without provider dispatch.

- `test_scheduler_status.py` verifies:
  - read-only `manager_historical_scheduler_status` collection;
  - automatic next-month selection visibility when daemon state is absent;
  - service template/env/wrapper readiness and required flag checks;
  - latest decision/provider-gate status reporting;
  - explicit deferred statuses for model activation, storage lifecycle mutation, and broker/account mutation.

- `test_dashboard_read_models.py` verifies:
  - manager-owned `historical_task_progress_summary` dashboard payload construction from read-only scheduler/status evidence;
  - optional stage-coverage counts in chart payloads;
  - CLI output shape without provider calls, model activation, broker execution, account mutation, or storage layout writes.

- `test_review_decision.py` verifies:
  - unified `review_decision` artifact construction;
  - activation records require approving review decisions;
  - `activation_record` links to its approved decision.

- `test_realtime_shadow_handoff.py` verifies:
  - paired realtime execution decision-input and model route-plan validation;
  - manager realtime shadow handoff receipt construction;
  - normalization into run/artifact/ready rows without provider calls, model activation, broker calls, or account mutation;
  - full execution fixture -> model route-plan -> manager receipt rehearsal CLI behavior;
  - CLI bundle output and forbidden action blocking.

- `test_task_control_plane.py` verifies:
  - generic `manager_request` validation;
  - component completion receipt normalization into run/artifact/ready rows;
  - component output and step-reference artifact discovery with duplicate collapse;
  - priority validation and global task-summary sort policy;
  - unified model-promotion review entrypoint policy;
  - failed receipts do not emit ready status;
  - malformed receipts are rejected;
  - JSONL request loading.

- `test_task_rehearsal.py` verifies:
  - deterministic in-memory task-system rehearsals;
  - ready, partial/review-required, and failed task-summary paths;
  - rehearsal CLI JSONL output shape.

- `test_target_context_review.py` verifies:
  - target-to-Layer-2 context mapping review request construction;
  - queued review artifact writing when no reviewed agent runner is configured;
  - configured local runner decision ingestion;
  - safety boundaries for proxy mappings without provider calls, model activation, broker/account mutation, storage lifecycle mutation, or Layer 1/2 universe edits.

- `test_trading_bigquery.py` verifies:
  - BigQuery query-result metadata parsing for dry-run byte estimates;
  - query request payload handling for `maximumBytesBilled` and dry-run flags.

- `test_trading_registry.py` verifies:
  - id-based `RegistryReader` lookup, required lookup, path, payload, key, and kind-filter behavior;
  - registry row mapping into `RegistryItem` objects;
  - source-level secret JSON alias parsing and id-based secret field resolution behavior;
  - SQL `kind` constraint alignment with `scripts/registry/kinds/*.md` and active `scripts/registry/current.csv` rows;
  - SQL `payload_format` constraint alignment with registered `kind=payload_format` rows;
  - SQL `artifact_sync_policy` constraint alignment with registered `kind=status_value` / `applies_to=artifact_sync_policy_type` rows;
  - test-script governance: first-party test scripts are documented here and are not registered as registry `script` rows.

## Run

From the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
