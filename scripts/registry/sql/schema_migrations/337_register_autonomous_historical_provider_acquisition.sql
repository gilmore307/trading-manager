-- Replace per-batch live-call approval gating with autonomous historical provider acquisition.
-- Historical provider/data acquisition may advance automatically under owner monitoring;
-- model activation/promotion and broker/order/account mutation remain separately blocked.

UPDATE trading_registry
SET payload = 'manager_provider_dispatch_summary_v1',
    applies_to = 'trading-manager;autonomous_historical_provider_acquisition_v1;layer_01_market_regime;01_feed_alpaca_bars',
    note = 'Manager-side summary for autonomous historical provider dispatch. Records request count, dispatch count, provider-call count, and per-request commands/receipt paths; it does not approve model activation, broker execution, order construction, or account mutation.',
    updated_at = NOW()
WHERE id = 'art_MMPD001';

UPDATE trading_registry
SET applies_to = 'trading-manager;scheduler;task_summary;manager_request_v1;ready_signal_v1;autonomous_historical_provider_acquisition_v1',
    note = 'One scheduler tick decision artifact: records allowed/backoff/executed status, resource gate state, selected work, next internal stage, command preview, and safety counters. Historical provider acquisition can advance automatically; model activation and broker/execution mutation remain false unless separately approved.',
    updated_at = NOW()
WHERE id = 'art_MSDV001';

UPDATE trading_registry
SET payload = '25 autonomous Alpaca bar requests for the reviewed layer_02_sector_context sector/industry ETF universe at 2016-01.',
    applies_to = 'layer_02_sector_context;01_feed_alpaca_bars;manager_request_v1;autonomous_historical_provider_acquisition_v1',
    note = 'Layer 2 data acquisition uses the reviewed layer_02_sector_context rows from the shared ETF universe. Preparing task keys is offline; provider dispatch is autonomous historical acquisition under scheduler/resource controls.',
    updated_at = NOW()
WHERE id = 'cfg_L2HT001';

UPDATE trading_registry
SET payload = REPLACE(payload, 'provider_calls_require_live_call_approval_v1', 'provider_calls_use_autonomous_historical_acquisition_v1'),
    applies_to = REPLACE(applies_to, 'live_call_approval_v1', 'autonomous_historical_provider_acquisition_v1'),
    note = 'Dataset expansion policy: manager decides which layer/role to expand next, prepares safe artifacts/payloads, and may automatically run historical provider acquisition. Expansion still does not approve model activation, promotion, or broker execution.',
    updated_at = NOW()
WHERE id = 'cfg_MDSE001';

UPDATE trading_registry
SET payload = REPLACE(payload, 'provider_calls_still_require_live_call_approval_v1', 'historical_provider_calls_run_autonomously_under_resource_controls'),
    note = 'Current pre-promotion scheduler policy: no production model/live trading capacity is active yet, so regular-session market-hours backoff is disabled to prioritize first promotable-model evidence. Host resource gates remain active; historical provider acquisition is autonomous; promotion review gates and broker/execution mutation gates remain hard. Re-enable market-hours protection before production model activation/live trading.',
    updated_at = NOW()
WHERE id = 'cfg_MMHP001';

UPDATE trading_registry
SET payload = 'autonomous_historical_provider_acquisition;continue_on_error_allowed_for_per_request_failures;failed_component_receipts_are_ingested;batch_failure_does_not_unlock_stage;broker_and_model_activation_still_forbidden',
    applies_to = 'manager_provider_dispatch_summary_v1;autonomous_historical_provider_acquisition_v1;component_completion_receipt_v1;manager_stage_coverage_v1',
    note = 'Manager may continue a historical provider batch after individual request failures so failed component receipts can be persisted and reviewed. This does not unlock downstream workflow stages, approve model activation, or permit broker/order/account mutation.',
    updated_at = NOW()
WHERE id = 'cfg_MGRPDISP001';

UPDATE trading_registry
SET key = 'PROVIDER_DISPATCH_EXECUTE_IS_AUTONOMOUS_HISTORICAL_ACQUISITION',
    payload = 'execute_provider_calls runs autonomous historical provider acquisition for bounded manager request ids; no live_call_approval_v1 or proposal validation is required',
    applies_to = 'manager_provider_dispatch_summary_v1;autonomous_historical_provider_acquisition_v1;provider_dispatch',
    note = 'Provider dispatch executes bounded historical provider requests automatically after manager task-key preparation. It strips old live-call policy refs from runtime task keys and preserves broker/model-activation prohibitions.',
    updated_at = NOW()
WHERE id = 'cfg_PDISP002';

UPDATE trading_registry
SET key = 'MANAGER_PROVIDER_ACQUISITION_DISPATCH',
    payload = 'PYTHONPATH=src python3 scripts/tasks/dispatch_and_reconcile_provider_stage.py',
    path = 'trading-manager/scripts/tasks/dispatch_and_reconcile_provider_stage.py',
    applies_to = 'trading-manager;autonomous_historical_provider_acquisition_v1;layer_01_market_regime;01_feed_alpaca_bars;manager_model_training_workflow_state_v1',
    note = 'Dispatches and reconciles autonomous historical provider acquisition for Layer 1/2 Alpaca bars. It does not require live_call_approval_v1 and does not activate models, execute broker orders, construct orders, or mutate accounts.',
    updated_at = NOW()
WHERE id = 'scr_MMPD001';

UPDATE trading_registry
SET applies_to = 'trading-manager;scheduler;historical_training;layer_01_market_regime;manager_scheduler_decision_v1;autonomous_historical_provider_acquisition_v1',
    note = 'Runs one capacity-aware scheduler tick. It applies resource gates, prepares Layer 1 task keys when needed, then can execute autonomous historical provider acquisition and downstream offline stages. It performs no model activation or broker/order/account mutation.',
    updated_at = NOW()
WHERE id = 'scr_MAST001';

UPDATE trading_registry
SET applies_to = REPLACE(applies_to, 'live_call_approval_required', 'autonomous_historical_provider_acquisition_v1'),
    updated_at = NOW()
WHERE id IN ('scr_L1HT001', 'scr_L2HT001');

UPDATE trading_registry
SET payload = 'owner_observed_autonomous_provider_data_acquisition',
    applies_to = 'autonomous_historical_provider_acquisition_v1;provider_dispatch;historical_backfill;manager_stage_coverage_v1',
    note = 'Historical provider acquisition may be dispatched and reconciled automatically while the owner observes and can intervene. Scope remains provider/data acquisition only; broker execution, model activation, promotion, and storage lifecycle mutation remain false unless separately approved.',
    updated_at = NOW()
WHERE id = 'trm_OWNEROBS001';

UPDATE trading_registry
SET applies_to = 'manager_model_training_workflow_state_v1;autonomous_historical_provider_acquisition_v1;provider_dispatch',
    note = 'Workflow-state counter for historical provider calls observed from ingested receipts, kept separate from offline/local stage counters so dashboards do not hide acquisition calls.',
    updated_at = NOW()
WHERE id = 'term_MWFSTATE003';

UPDATE trading_registry
SET applies_to = 'manager_provider_dispatch_summary_v1;manager_stage_coverage_v1;autonomous_historical_provider_acquisition_v1',
    note = 'Provider execution guard used by autonomous provider execution command templates. When enabled, execution refuses request ids already ready or reviewed-terminal in stage coverage and refuses to continue while unreviewed failed stage requests exist.',
    updated_at = NOW()
WHERE id = 'trm_LCAP007';
