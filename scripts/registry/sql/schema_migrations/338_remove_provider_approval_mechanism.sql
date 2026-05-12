-- Remove the retired live_call_approval_v1 approval mechanism from active registry rows.
-- Historical provider/data acquisition now advances autonomously under manager
-- resource controls, bounded request ids, terminal-coverage guards, receipts,
-- and failure review. Broker/order/account mutation, model activation/promotion,
-- and storage lifecycle mutation remain separately gated.

DELETE FROM trading_registry
WHERE id IN (
  'art_LCA001',
  'cfg_LCA001',
  'scr_LCAPKT005',
  'scr_LCAP003',
  'scr_LCAP004',
  'scr_LCA001',
  'scr_LCAP001',
  'scr_LCAP005',
  'scr_LCAP002',
  'trm_LCAP003',
  'trm_LCAP005',
  'term_LCAPKT004',
  'trm_LCAP004',
  'trm_LCAP001',
  'trm_LCAP002',
  'trm_LCAP006'
);

UPDATE trading_registry
SET key = 'PROVIDER_CALL_GUARDRAILS_POLICY',
    payload = REPLACE(payload, 'live_calls_disabled_by_default;', ''),
    applies_to = REPLACE(REPLACE(applies_to, 'live_call_policy', 'historical_provider_acquisition'), 'live_call_approval_v1', 'autonomous_historical_provider_acquisition_v1'),
    note = 'Provider/API access guardrails for automated historical acquisition: provider allowlists, request/window bounds, rate-limit backoff, retry discipline, resource controls, receipts, and failure registration. This is not a manual approval mechanism.',
    updated_at = NOW()
WHERE id = 'cfg_MSH008';

UPDATE trading_registry
SET payload = REPLACE(payload, 'live_calls_disabled_by_default;', ''),
    applies_to = REPLACE(applies_to, 'live_call_policy', 'historical_provider_acquisition'),
    note = 'Production hardening policy for trading-data/provider access. Historical provider acquisition can run autonomously under manager controls; production model activation and broker/account mutation remain outside this policy.',
    updated_at = NOW()
WHERE id = 'cfg_MSH006';

UPDATE trading_registry
SET payload = REPLACE(payload, 'live-call approval gate removed; ', ''),
    note = 'Manager control-plane closeout status after removing the per-batch provider-call approval mechanism. Historical provider acquisition is autonomous under resource/coverage controls; model activation and broker/account mutation remain separately blocked.',
    updated_at = NOW()
WHERE id = 'cfg_MCO001';

UPDATE trading_registry
SET applies_to = REPLACE(applies_to, 'live_call_approval_v1', 'autonomous_historical_provider_acquisition_v1'),
    note = 'Manager-owned review for Layer 8 option-expression acquisition. Active target chains are prepared for autonomous option-snapshot acquisition; no manual live_call_approval_v1 packet is required.',
    updated_at = NOW()
WHERE id IN ('scr_L8GATE001', 'term_L8GATE001');

UPDATE trading_registry
SET applies_to = REPLACE(applies_to, 'live_call_approval_v1', 'autonomous_historical_provider_acquisition_v1'),
    note = 'Builds the controlled information pass report and optional plan-only provider dispatch preview. It performs no provider calls unless a dedicated dispatch command is executed.',
    updated_at = NOW()
WHERE id = 'scr_MGRINFO001';

UPDATE trading_registry
SET applies_to = 'manager_stage_run_controller_receipt_v1;manager_stage_run_dashboard_v1;autonomous_historical_provider_acquisition_v1;stage_control_loop',
    note = 'Callable manager entrypoint that can execute one bounded autonomous provider-dispatch slice and writes a receipt/dashboard. It does not activate models, construct/execute broker orders, mutate accounts, or perform storage lifecycle mutation.',
    updated_at = NOW()
WHERE id = 'scr_SRCT001';

UPDATE trading_registry
SET applies_to = 'manager_stage_run_dashboard_v1;stage_coverage;autonomous_historical_provider_acquisition_v1;provider_dispatch;stage_reconcile',
    note = 'Callable manager entrypoint that writes or prints the stage-run dashboard/receipt with coverage and the next autonomous provider-dispatch preview.',
    updated_at = NOW()
WHERE id = 'scr_SRDB001';

UPDATE trading_registry
SET applies_to = 'manager_stage_run_dashboard_v1;autonomous_historical_provider_acquisition_v1;stage_control_loop',
    note = 'Receipt for one manager stage-run controller step. The controller may execute a bounded autonomous provider-dispatch slice, while model activation, broker/order/account mutation, and storage lifecycle mutation remain forbidden here.',
    updated_at = NOW()
WHERE id = 'trm_SRCT001';

UPDATE trading_registry
SET applies_to = 'manager_stage_coverage_v1;autonomous_historical_provider_acquisition_v1;manager_provider_dispatch_summary_v1;manager_provider_stage_reconcile_v1;trading_manager.failure_register',
    note = 'Single operator-facing dashboard/receipt for one manager provider-stage/month. It summarizes coverage, the next autonomous dispatch preview, observed provider calls, and evidence refs.',
    updated_at = NOW()
WHERE id = 'trm_SRDB001';

UPDATE trading_registry
SET payload = 'execute_provider_calls runs autonomous historical provider acquisition for bounded manager request ids; no per-batch approval artifact or proposal validation is required',
    note = 'Provider dispatch executes bounded historical provider requests automatically after manager task-key preparation. It strips retired approval policy refs from runtime task keys and preserves broker/model-activation prohibitions.',
    updated_at = NOW()
WHERE id = 'cfg_PDISP002';
