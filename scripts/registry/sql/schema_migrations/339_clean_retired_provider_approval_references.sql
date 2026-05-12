-- Clean remaining active registry wording after retiring the historical provider
-- approval mechanism. Provider acquisition is autonomous under manager controls;
-- model activation, broker/order/account mutation, and storage lifecycle mutation
-- remain separately gated.

UPDATE trading_registry
SET payload = 'provider_dispatch_managed_by_manager_controls;retry_backoff_required_for_provider_calls;checkpoint_resume_required_for_segmented_runs;durable_manifest_required;ready_signal_required_for_downstream_consumption;secrets_by_alias_only;ignored_local_storage_not_durable',
    applies_to = 'trading-data;trading-manager;production_hardening;data_source;data_feed;control_plane;historical_provider_acquisition',
    note = 'Production hardening policy for trading-data/provider access. Historical provider acquisition runs autonomously under manager controls; production model activation and broker/account mutation remain outside this policy.',
    updated_at = NOW()
WHERE id = 'cfg_MSH006';

UPDATE trading_registry
SET payload = 'current_manager_control_plane_phase_closed;task_system_mvp_implemented;global_task_summary_implemented;monthly_backfill_planning_implemented;request_payload_materialization_implemented;dry_run_handoff_validation_implemented;unified_model_promotion_route_implemented;review_decision_activation_artifacts_implemented;autonomous_historical_provider_acquisition_enabled;no_broker_execution_enabled;no_production_activation_implied',
    applies_to = 'trading-manager;control_plane;closeout;task_system;model_promotion;autonomous_historical_provider_acquisition',
    note = 'Manager control-plane closeout status after removing the per-batch provider-call approval mechanism. Historical provider acquisition is autonomous under resource/coverage controls; model activation and broker/account mutation remain separately blocked.',
    updated_at = NOW()
WHERE id = 'cfg_MCO001';

UPDATE trading_registry
SET note = 'Manager-owned review for Layer 8 option-expression acquisition. Active target chains are prepared for autonomous option-snapshot acquisition; no manual provider approval packet is required.',
    updated_at = NOW()
WHERE id IN ('scr_L8GATE001', 'term_L8GATE001');

UPDATE trading_registry
SET note = 'Dispatches and reconciles autonomous historical provider acquisition for Layer 1/2 Alpaca bars. It requires no manual provider approval artifact and does not activate models, execute broker orders, construct orders, or mutate accounts.',
    updated_at = NOW()
WHERE id = 'scr_MMPD001';

UPDATE trading_registry
SET note = 'Callable manager entrypoint for offline reconciliation after a provider batch. It records existing receipts, writes coverage reports, and can refresh workflow state; it never dispatches providers or performs broker/model/storage lifecycle mutations.',
    updated_at = NOW()
WHERE id = 'scr_RECON001';

UPDATE trading_registry
SET id = 'trm_TCEG001',
    updated_at = NOW()
WHERE id = 'trm_LCAP007';
