# Scripts

`scripts/` contains executable entrypoints for registry maintenance and manager task operations.

## Boundary

- Scripts may import `src/` packages.
- `src/` must not import scripts.
- Stable automation-facing commands should be registered as `kind=script` when needed.
- Registry SQL and current row inventory live under `scripts/registry/`.

## Registry Commands

Clean local/CI verification without DB credentials:

```bash
python3 scripts/registry/check_registry_current_matches_db.py --allow-missing-db
```

Operator/server verification and mutation with DB access:

```bash
python3 scripts/registry/sync_registry.py --dry-run
python3 scripts/registry/check_registry_current_matches_db.py
python3 scripts/registry/sync_registry.py
python3 scripts/registry/sync_registry.py --export-only
```

## Task Command Groups

| Group | Scripts |
|---|---|
| Request lifecycle | `submit_manager_requests.py`, `materialize_request_payloads.py`, `validate_request_handoff.py`, `record_completion_receipt.py`, `list_task_summary.py`, `rehearse_task_system.py` |
| Historical planning | `plan_monthly_backfill.py`, `prepare_layer_one_historical_training.py`, `prepare_layer_two_historical_training.py`, `plan_model_training_workflow.py`, `advance_model_training_workflow.py` |
| Scheduler/runtime | `run_automation_scheduler.py`, `run_automation_scheduler_daemon.py`, `inspect_historical_scheduler_status.py`, `build_historical_task_progress_summary.py`, `run_stage_controller.py`, `summarize_stage_run.py` |
| Provider/reconcile | `dispatch_provider_acquisition.py`, `dispatch_and_reconcile_provider_stage.py`, `reconcile_provider_stage.py`, `dispatch_event_feed_backfill.py`, `prepare_residual_event_feed_backfill.py`, `prepare_event_family_modelability_acquisition.py`, `build_event_family_modelability_evidence_packet.py` |
| Model/evidence | `collect_dataset_evidence.py`, `plan_dataset_expansion.py`, `execute_model_training_stage.py`, `plan_model_promotion_review.py`, `build_agent_model_promotion_decision.py`, `build_review_decision.py` |
| Model-specific helpers | `execute_layer_two_feature_generation.py`, `prepare_option_chain_source_acquisition.py`, `dispatch_option_chain_source_acquisition.py`, `materialize_layer_three_target_state_inputs.py`, `review_target_m02_context_mapping.py`, `execute_m05_option_expression_feature_generation.py`, `run_model_group_replay_contract_paths.py`, `materialize_model_03_event_impact_inputs.py`, `plan_event_model_regeneration.py`, `invalidate_residual_event_downstream_outputs.py` |
| Failure/recovery | `register_failure.py`, `list_failure_register.py`, `call_agent_for_error.py`, `list_agent_errors.py`, `run_agent_error_agent.py`, `run_safe_error_repair.py` |
| Realtime handoff validation | `record_realtime_shadow_handoff.py`, `rehearse_realtime_shadow_handoff.py` |
| External evidence helpers | `prepare_nasdaq_earnings_baseline_snapshots.py` |

## Safety

Planning scripts should default to dry-run or no-provider behavior. Provider calls, persistent writes, storage lifecycle mutation, model activation, and broker/account mutation require their documented explicit gates; broker/account mutation is never manager-owned.

## Verification

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall -q src scripts
```
