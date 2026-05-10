# Tests

`tests/` owns first-party tests for the `trading-manager` source packages and repository governance checks.

## Boundary

- Test scripts are repository-local verification assets, not registry entries.
- Do not register test files as registry `script` rows.
- Every first-party `test_*.py` script in this directory must be listed in the inventory below with what it verifies.
- Update this README whenever a test script is added, renamed, split, merged, or removed.

## Inventory

- `test_model_promotion.py` verifies:
  - unified model promotion review request planning;
  - registered model target coverage across Layers 1-8;
  - one shared `model_promotion_review_v1` request kind for all model layers.

- `test_live_call_gate.py` verifies:
  - `live_call_approval_v1` validation for bounded non-dry-run provider acquisition requests;
  - rejection of dry-run requests, missing live-call gate policy, wrong provider scope, over-wide windows, over-count batches, and broker-execution approval.

- `test_historical_training.py` verifies:
  - manager-owned Layer 1 historical-training batch preparation;
  - full market-regime ETF universe request expansion;
  - task-key payload materialization and handoff validation without provider calls, model activation, or broker execution.

- `test_monthly_backfill.py` verifies:
  - monthly window generation;
  - accepted `2016-01` common start behavior;
  - OKX crypto joining later at `2018-01`;
  - current-only feeds staying out of historical backfill requests;
  - dry-run `manager_request_v1` JSONL shape.

- `test_request_payloads.py` verifies:
  - `storage://trading-manager/...` parameter refs resolve to local storage-root paths;
  - monthly backfill requests materialize component-readable `task_key.json` payloads;
  - request-scoped `input_binding_v1` metadata captures parameter payload refs and hashes;
  - all default `2016-01` monthly backfill feeds receive required starter params.

- `test_request_handoff.py` verifies:
  - materialized request payloads load through component `build_context` without dispatch/provider calls;
  - hash-backed `input_binding_v1` metadata must match the local payload;
  - live-call-enabled payloads are rejected by the dry-run handoff validator.

- `test_scheduler.py` verifies:
  - regular-trading-day-only market-hours protection;
  - weekend and market-holiday exemptions from the 09:20-16:10 ET pause window;
  - resource-pressure gating that reserves live-system capacity;
  - scheduler ready/backoff/executed decisions for safe offline Layer 1 preparation without provider dispatch.

- `test_scheduler_daemon.py` verifies:
  - `manager_scheduler_daemon_state_v1` checkpoint round-tripping and resume-scope updates;
  - single-instance lock behavior;
  - error checkpointing for restart-safe failure visibility;
  - persistent daemon loop state/log writing without provider dispatch.

- `test_review_decision.py` verifies:
  - unified `review_decision_v1` artifact construction;
  - activation records require approving review decisions;
  - `activation_record_v1` links to its approved decision.

- `test_task_control_plane.py` verifies:
  - generic `manager_request_v1` validation;
  - component completion receipt normalization into run/artifact/ready rows;
  - priority validation and global task-summary sort policy;
  - unified model-promotion review entrypoint policy;
  - failed receipts do not emit ready status;
  - malformed receipts are rejected;
  - JSONL request loading.

- `test_task_rehearsal.py` verifies:
  - deterministic in-memory task-system rehearsals;
  - ready, partial/review-required, and failed task-summary paths;
  - rehearsal CLI JSONL output shape.

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
