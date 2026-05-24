-- Register C01 sector opportunity mix semantics.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'fld_EXECRTC011',
  'field',
  'SECTOR_OPPORTUNITY_MIX',
  'field_name',
  'sector_opportunity_mix',
  'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/decisions.py',
  'execution_intake_snapshot;component_01_intake;sector_context_state;model_02_sector_context;component_02_entry',
  'sync_artifact',
  'C01 Intake field listing sufficiently strong sectors/themes and normalized opportunity weights derived from relative M02 strength. It is an opportunity map for C02, not a final position weight, order quantity, or risk allocation instruction.'
)
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = CURRENT_TIMESTAMP;

UPDATE trading_registry
SET note = 'Execution runtime contract emitted by C01 Intake for account balance state, current holdings, watch targets, sector opportunity mix, and account-sleeve candidate filtering. It does not allocate risk budget, size positions, decide entries, manage exits, construct orders, or mutate broker/account state.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC003';

UPDATE trading_registry
SET note = 'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. C01 Intake reads account state, current holdings, watch targets, and sector opportunity mix only; it does not allocate risk budget or manage positions. trading-evaluation owns orchestration and judgment, not duplicated trading decisions. Runtime decisions must keep crypto and equity/options in independent account sleeves without cross-account collateral, buying-power, position, or risk-budget netting.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC001';
