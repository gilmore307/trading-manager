-- Register manager automation scheduler policy for continuous historical training with live-system protection.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MASP001',
    'config',
    'MANAGER_AUTONOMOUS_SCHEDULER_POLICY',
    'text',
    'continuous_safe_work;data_acquisition_to_feature_to_model_to_evaluation_to_promotion_review;approval_gated_provider_dispatch;promotion_review_gated_activation;execution_priority_reserved;no_manual_one_task_prompting',
    'trading-manager/docs/98_automation_scheduler.md',
    'trading-manager;scheduler;historical_training;manager_request_v1;task_summary;model_promotion_review_v1',
    'sync_artifact',
    'Target manager scheduler policy: keep safe historical training and maintenance work progressing automatically across data acquisition, feature generation, model training, evaluation, and promotion-review preparation while preserving approval and execution gates.'
  ),
  (
    'cfg_MRBP001',
    'config',
    'MANAGER_RESOURCE_BUDGET_POLICY',
    'text',
    'live_trading_capacity_reserved;historical_worker_count_capacity_adaptive;pause_or_throttle_on_resource_pressure;prefer_restartable_receipt_backed_batches;provider_rate_limits_respected',
    'trading-manager/docs/98_automation_scheduler.md',
    'trading-manager;scheduler;resource_budget;historical_training;live_monitoring;execution_system',
    'sync_artifact',
    'Resource-budget policy for manager automation: historical training can use concurrency only after reserving live monitoring/order-routing capacity and must throttle under CPU, memory, disk, database, provider, or live-system pressure.'
  ),
  (
    'cfg_MMHP001',
    'config',
    'MANAGER_MARKET_HOURS_HISTORICAL_PAUSE_POLICY',
    'text',
    'america_new_york_regular_equity_session_protection;09:20-16:10_et;pause_new_historical_provider_batches;pause_cpu_heavy_feature_model_eval;allow_light_bookkeeping_only;manual_override_requires_review',
    'trading-manager/docs/98_automation_scheduler.md',
    'trading-manager;scheduler;market_hours;historical_training;live_monitoring;execution_system',
    'sync_artifact',
    'Default market-hours protection policy: during regular US equity session protection windows, historical acquisition/modeling jobs pause or heavily throttle so live monitoring and execution retain priority.'
  ),
  (
    'trm_MSWL001',
    'term',
    'MANAGER_SCHEDULER_WORK_LOOP',
    'text',
    'inspect_summary_find_safe_work_check_gates_dispatch_allowed_request_record_receipt_continue_or_backoff',
    'trading-manager/docs/98_automation_scheduler.md',
    'trading-manager;scheduler;task_summary;manager_request_v1;ready_signal_v1;artifact_ref_v1',
    'sync_artifact',
    'Durable manager scheduler loop semantics: inspect state, choose the next safe dependency-ready item, check approval/resource/market-hour gates, dispatch only allowed work, record receipts, and back off with an explicit reason when no safe work exists.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
