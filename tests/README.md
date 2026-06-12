# Tests

`tests/` contains unit and governance tests for `trading-manager`.

## Rules

- Add or update a test when behavior, contracts, registry rules, or scheduler gates change.
- Keep tests deterministic and local by default.
- Tests must not call providers, mutate broker/account state, or require secrets unless explicitly isolated and skipped by default.
- Update this README whenever a `test_*.py` file is added, renamed, split, merged, or removed.

## Run

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Test Files

- `test_agent_error_handler.py`
- `test_agent_repair_closure.py`
- `test_dashboard_read_models.py`
- `test_dataset_evidence.py`
- `test_dataset_expansion.py`
- `test_event_feed_backfill.py`
- `test_event_feed_dispatch.py`
- `test_event_model_regeneration_plan.py`
- `test_failure_register.py`
- `test_governance_checks.py`
- `test_historical_training.py`
- `test_information_pass.py`
- `test_layer_four_event_failure_features.py`
- `test_m05_option_expression_feature_stage.py`
- `test_residual_event_governance_inputs.py`
- `test_layer_three_target_state.py`
- `test_model_group_attribution.py`
- `test_model_group_evaluation.py`
- `test_model_group_replay.py`
- `test_model_group_replay_contract_paths.py`
- `test_model_group_replay_dataset.py`
- `test_model_group_replay_option_features.py`
- `test_model_group_rerun.py`
- `test_model_promotion.py`
- `test_model_worker_target_queue.py`
- `test_model_training_invalidation.py`
- `test_model_training_state.py`
- `test_model_training_workflow.py`
- `test_monthly_backfill.py`
- `test_nasdaq_earnings_baseline.py`
- `test_option_chain_source_acquisition.py`
- `test_post_model_schema.py`
- `test_provider_dispatch.py`
- `test_realtime_shadow_handoff.py`
- `test_request_handoff.py`
- `test_request_payloads.py`
- `test_request_schema_validation.py`
- `test_review_decision.py`
- `test_safe_error_repair.py`
- `test_scheduler.py`
- `test_scheduler_daemon.py`
- `test_scheduler_locks.py`
- `test_scheduler_status.py`
- `test_source_existing_bootstrap.py`
- `test_stable_semantic_ids.py`
- `test_stage_coverage.py`
- `test_stage_executor.py`
- `test_stage_reconcile.py`
- `test_stage_run_controller.py`
- `test_stage_run_dashboard.py`
- `test_target_context_review.py`
- `test_task_control_plane.py`
- `test_task_progress.py`
- `test_task_rehearsal.py`
- `test_trading_bigquery.py`
- `test_trading_economics_calendar.py`
- `test_trading_registry.py`
