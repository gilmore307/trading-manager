-- Register missing-data tolerance and historically absent data handling policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MGRMDT001',
    'config',
    'MODEL_MISSING_DATA_TOLERANCE_POLICY',
    'text',
    'valid_absent_history_is_terminal_evidence;no_data_not_yet_listed_is_not_provider_failure;zero_row_receipts_may_count_as_ready_coverage;coverage_and_data_quality_scores_carry_missingness;promotion_gates_may_block_low_coverage;do_not_fabricate_bars',
    'trading-model/docs/02_layer_01_market_regime.md;trading-manager/docs/95_task_system.md',
    'manager_stage_coverage_v1;ready_signal_v1;model_01_market_regime;model_01_market_regime_diagnostics;model_promotion_metric',
    'sync_artifact',
    'Historical model construction must tolerate explainable missing observations. Not-yet-listed symbols and reviewed provider no-data responses should become explicit coverage/missingness evidence rather than fabricated data or unbounded retries; low coverage can still block promotion/downstream unlocks.'
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
