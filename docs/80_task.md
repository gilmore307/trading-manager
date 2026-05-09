# Task

## Active Tasks

- None.

## Queued Tasks

- Use `docs/96_model_promotion.md`, `scripts/tasks/plan_model_promotion_review.py`, and `scripts/tasks/build_review_decision.py` as the single manager-side route for every model-layer promotion review request/decision artifact.
- Before enabling live provider calls, define and review the live-call approval gate that converts dry-run backfill requests into actual component dispatch.

## Deferred Until Manager Phase

- Physical execution queue and worker implementation beyond durable `manager_request_v1` / run-manifest SQL facts.
- Migration criteria from legacy local data-production staging files into durable `trading-storage` SQL/artifact contracts.

## Open Gaps

- Broker/order-construction implementation after execution-side `trade_risk_cap` validation.
- Durable object-store/SQL partitioning details beyond current storage-owned filesystem payload helper and manager SQL summary rows.

## Recently Accepted

- Closed all seven bounded `2016-01` dry-run monthly request/receipt paths: storage-owned receipt payloads were materialized in `trading-storage`, manager normalized them into SQL run/artifact/ready rows, and `task_summary` now reports each dry-run request as `ready` with `artifact_count=1`; no provider calls, component runs, or production data outputs occurred.
- Registered storage receipt-payload and execution risk-cap validation entrypoints through migration `262_register_storage_receipt_and_risk_cap_entrypoints.sql`.
- Added concrete unified review decision artifacts: `review_decision_v1` and `activation_record_v1` builders/tests, plus script `scripts/tasks/build_review_decision.py`. Activation records require an approving review decision.
- Added component-facing handoff validation: `scripts/tasks/validate_request_handoff.py` loads materialized request payloads, verifies hash-backed input bindings and dry-run policy, and calls only target component `build_context` without dispatching work or calling providers.
- Added request payload materialization: `scripts/tasks/materialize_request_payloads.py` writes component-readable `task_key.json` payloads behind `manager_request.parameter_ref` and can persist request-scoped `input_binding_v1` metadata without provider calls or component dispatch.
- Added deterministic task-system rehearsal entrypoint: `scripts/tasks/rehearse_task_system.py` exercises manager request, component receipt, run manifest, artifact ref, ready signal, and task-summary-like rows without provider calls or SQL writes.
- Added unified model promotion review entrypoint: all model layers now use `model_promotion_review_v1` manager requests through `scripts/tasks/plan_model_promotion_review.py`; model-specific code only produces evidence/adapters.
- Added global task summary: `trading_manager.task_summary` derives every manager request's current status, latest run, latest ready signal, artifact count, priority, and priority rank for ordered dashboards/CLIs.
- Added unified manager task-system request/receipt handling: manager requests are validated/persisted centrally, and component completion receipts normalize into run-manifest, artifact-ref, and ready-signal facts.
- Added monthly historical backfill planning: common start `2016-01`, OKX crypto joins at `2018-01`, and current-only feeds stay out of historical point-in-time backfill until a new route is accepted.
- Implemented and registered the concise MVP manager/control-plane SQL tables: `trading_manager.manager_request`, `trading_manager.input_binding`, `trading_manager.run_manifest`, `trading_manager.run_step`, `trading_manager.artifact_ref`, and `trading_manager.ready_signal`. `component_ref_v1` remains registry-backed fields rather than a separate component catalog table.
- Added first-principles manager contract design in `docs/93_contracts.md`, including core MVP contracts, evaluation/promotion contracts, downstream handoff contracts, ownership boundaries, lifecycle relationships, persistence policy, and implementation order.
- Registered manager/storage V1 handoff contracts and hardening policies: `manager_request_v1`, `run_manifest_v1`, `artifact_ref_v1`, `ready_signal_v1`, live-call guardrails, checkpoint/resume policy, and data-production hardening policy.
- Registered full production-promotion closeout decisions: Layers 1-2 have real database evidence and persisted deferred decisions; Layer 3 now has real production-evaluation substrate but remains deferred by upstream approvals/calibration; Layers 4-8 have persisted blocked eval runs, metrics, candidates, and reviewer-agent deferred decisions for missing production eval substrate; no production activation is approved.
- Registered `trading-data` closeout readiness policies: data-source/model-input design closed, ETF holdings default visibility at next regular US session open after `as_of_date`, and `equity_abnormal_activity_conservative_v1` as conservative/non-production-calibrated until reviewed historical evidence exists.
- Registered production-promotion readiness checklist/status matrix terms for Layers 1-8 and mandatory `trade_risk_cap` execution-safety vocabulary. This starts the manager/control-plane phase without implying production model approval or live execution enablement.
- Registered all current `task_key.json` and `completion_receipt.json` field names as `kind=field` rows.
- Updated task key/receipt templates so stable task keys can have multiple run entries in completion receipts.
- Simplified `task_key.json` and `completion_receipt.json` to minimal operational fields.
- Updated data task templates so sources default to one `pipeline.py` with fetch/clean/save/receipt step functions.
- Added data task templates for task keys, source docs, fetch/clean/save specs, completion receipts, and fixture policy.
- Registered the earlier draft development-storage-root contract, later pruned it from active registry rows, and kept local `storage/` as an ignored legacy runtime path for unmigrated source sources.
- Registered control-plane-driven historical data task workflow terms for task key files and completion receipts.
- Registered FOMC calendar, official macro release calendar discovery, and ETF issuer holdings source terms.
- Registered U.S. Treasury Fiscal Data as an open/no-key provider term with official documentation path.
- Added official documentation URLs to registered provider term paths while keeping secret config paths pointed at local JSON files.
- Registered FRED, Census, BEA, and BLS source-level secret aliases for macro/economic data acquisition.
- Registered ThetaData provider terminology for options data; credentials/JAR placement deferred.
- Registered Alpaca source-level secret alias for stock/ETF bars, quotes, trades, and news data acquisition.
- Consolidated OKX and GitHub secret handling to one JSON secret file per source and registered source-secret JSON field names.
- Moved OKX allowlisted IPv4 and API key remark into the source-level OKX JSON secret file contract.
- Defined test-script boundary: test scripts stay out of registry `script` rows and are inventoried in their test-directory README.
- Removed registry kind vocabulary validators from the runtime helper package; tests now compare SQL kind constraints with `scripts/registry/kinds/*.md`.
- Registered legal `payload_format` values as `payload_format` registry rows and removed payload-format validators from the runtime helper surface.
- Expanded registry `payload_format` beyond `text`/`file` and backfilled current rows with narrower formats.
- Removed the old non-Python registry helper implementation; helper code is now Python-only.
- Added formal Python registry helper package and pointed registry script rows at Python helper methods.
- Created initial docs spines for component repositories including the now-merged manager, storage, derived, model, execution, and dashboard repositories.
- Defined repository visibility policy: trading repositories stay private unless the owner explicitly approves a visibility change.
- Defined helper distribution boundary: cross-repository runtime helpers use the Python helper package.
- Defined shared environment baseline: Python 3.12, `.venv`, `pip`, and reviewed `requirements.txt`.
- Split `trading-manager` platform-function guides into `docs/90_helpers.md`, `docs/91_registry.md`, and `docs/92_templates.md`.
- Added scripts/platform guide docs so platform-specific rules have focused guides separate from task/decision/memory and layer workflow docs.
- Moved registry kind boundary files into `scripts/registry/kinds/`; `scripts/registry/rules/` remains for review artifacts.
- Registered the active trading repositories as `repo` rows in `scripts/registry/current.csv`; later merged source/derived data-production boundaries back into `trading-data`.
- Registered `HELPER_REGISTRY_EXPORT_CURRENT_CSV` for regenerating `scripts/registry/current.csv`.
- Standardized registered helper surface to four id-only helpers: key, payload, path, and secret text by config id.
- Backfilled `applies_to` for every active field registry entry and added a SQL check constraint to prevent blank field scopes.
- Registered id-first path helper methods in the SQL registry.
- Added nullable registry `applies_to` column for field usage/source scope.
- Updated secret resolver helper to prefer config ids; later standardized the public helper surface to id-input only.
- Added nullable registry `path` column and id-first path helper APIs.
- Removed `path` as a registry kind and merged standalone root-path entries into their owning entity rows.
- Restored `TAILSCALE` and `SMB` as active `term` entries.
- Moved artifact/manifest/ready-signal/request contract placeholders from `docs/` to `trading-storage/main/templates/contracts/`.
- Added registry kind boundaries for `artifact_type`, `manifest_type`, `ready_signal_type`, and `request_type`.
- Removed canceled-project registry entries and regenerated `scripts/registry/current.csv`.
- Corrected registry shape so Markdown kind files define kind boundaries while SQL migrations own concrete entries.
- Added SQL-to-CSV registry snapshot generation at `scripts/registry/current.csv`.
- Added registry kind boundary overlap review.
- Migrated former standalone registry into `trading-manager`: SQL migrations own concrete entries, Markdown kind files own boundaries.

- Defined initial `trading-manager` docs spine and pushed initial trading repositories to GitHub.
- Initial repository list approved:
  - `trading-manager`
  - `trading-data`
  - `trading-storage`
  - `trading-model`
  - `trading-execution`
  - `trading-dashboard`
