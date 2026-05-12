-- Final wording cleanup for autonomous historical provider dispatch.

UPDATE trading_registry
SET note = 'Durable checkpoint for the manager-owned Layer 1-8 historical-training workflow. Records stage status, commands, blockers, review refs, receipt refs, artifact refs, and next-stage progression.',
    updated_at = NOW()
WHERE id = 'art_MMTW002';

UPDATE trading_registry
SET payload = 'execute_provider_calls runs autonomous historical provider acquisition for bounded manager request ids; no per-batch manual gate is required',
    note = 'Provider dispatch executes bounded historical provider requests automatically after manager task-key preparation. It strips retired provider-policy refs from runtime task keys and preserves broker/model-activation prohibitions.',
    updated_at = NOW()
WHERE id = 'cfg_PDISP002';

UPDATE trading_registry
SET note = 'Manager-owned review for Layer 8 option-expression acquisition. Active target chains are prepared for autonomous option-snapshot acquisition; no manual provider gate is required.',
    updated_at = NOW()
WHERE id IN ('scr_L8GATE001', 'term_L8GATE001');

UPDATE trading_registry
SET note = 'Refreshes the durable Layer 1-8 workflow checkpoint, ingests component receipts, records review refs, and selects the next safe or guarded stage without provider calls, model activation, or broker execution.',
    updated_at = NOW()
WHERE id = 'scr_MMTW002';

UPDATE trading_registry
SET note = 'Dispatches and reconciles autonomous historical provider acquisition for Layer 1/2 Alpaca bars. It requires no manual provider gate and does not activate models, execute broker orders, construct orders, or mutate accounts.',
    updated_at = NOW()
WHERE id = 'scr_MMPD001';

UPDATE trading_registry
SET note = 'Executes one ready safe offline workflow stage after scheduler gates, writes logs and a component receipt, and refuses unsafe mutation stages.',
    updated_at = NOW()
WHERE id = 'scr_MMSE001';
