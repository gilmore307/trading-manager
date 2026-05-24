-- Register C02 as underlying entry-thesis suitability, not expression or order selection.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_EXECRTC005',
  'config',
  'C02_ENTRY_THESIS_POLICY',
  'text',
  'consume_c01_watch_targets_only;underlying_entry_thesis_only;status_suitable_deferred_rejected;no_balance_check;no_option_expression;no_direct_order_intent;suitable_routes_to_c04',
  'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/decisions.py',
  'component_02_entry;entry_decision;component_04_option_review;component_06_order_intent',
  'sync_artifact',
  'C02 Entry consumes C01 watch targets and decides only whether the underlying has a suitable entry thesis. It emits suitable, deferred, or rejected with entry direction, entry zone, target/take-profit, model invalidation, hard stop, horizon, and suitability score. C02 does not check account balance, choose option versus stock expression, select contracts, size positions, build orders, or directly authorize C06 order intents; suitable entries route to C04 expression review.'
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
SET note = 'Execution runtime contract emitted by C02 Entry for underlying entry-thesis suitability only. Status is suitable, deferred, or rejected. A suitable thesis includes direction, entry zone, target or take-profit zone, model invalidation price, hard stop price, horizon when available, and suitability score. C02 consumes C01 watch targets only, does not call Layer 9 or Layer 10, does not choose option versus stock expression, does not check account balance, and does not directly authorize order intents.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC004';

UPDATE trading_registry
SET note = 'Accepted concise numbered intraday execution component sequence. C01 Intake owns account/watch-target intake; C02 Entry owns underlying entry-thesis suitability; C04 owns option/underlying expression review; downstream lifecycle, failure review, order intent, and execution gates own their separate boundaries. component_id values follow the model-aligned physical naming pattern component_01_* through component_07_*.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC003';
