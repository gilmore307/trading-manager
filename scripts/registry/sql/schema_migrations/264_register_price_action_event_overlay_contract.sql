-- Register Layer 4 price-action event overlay contract for false-breakout style events.

UPDATE trading_registry
SET note = 'Classification value: stable lowercase token for event_category_type. Accepted values include macro_data, macro_news, sector_news, symbol_news, sec_filing, option_abnormal_activity, equity_abnormal_activity, and price_action.',
    updated_at = NOW()
WHERE key = 'EVENT_CATEGORY_TYPE';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_EVCAT001',
    'config',
    'EVENT_CATEGORY_TYPE_VALUES',
    'text',
    'macro_data;macro_news;sector_news;symbol_news;sec_filing;option_abnormal_activity;equity_abnormal_activity;price_action',
    'trading-data/src/data_source/source_04_event_overlay/README.md',
    'source_04_event_overlay;event_category_type;event_overlay_model;event_context_vector',
    'sync_artifact',
    'Allowed event_category_type values for source_04_event_overlay overview rows. price_action is a source-detector event category for false-breakout, failed-breakdown, liquidity-sweep, bull-trap, and bear-trap evidence; it is not a separate model layer.'
  ),
  (
    'cfg_PAE001',
    'config',
    'PRICE_ACTION_EVENT_TYPES',
    'text',
    'false_breakout;false_breakdown;liquidity_sweep_high;liquidity_sweep_low;bull_trap;bear_trap',
    'trading-model/docs/05_layer_04_event_overlay.md',
    'price_action;source_04_event_overlay;event_overlay_model;event_context_vector;equity_abnormal_activity_event',
    'sync_artifact',
    'Canonical Layer 4 price-action event tokens. They describe board/tape behavior used as event overlay evidence, not buy/sell/hold decisions or execution instructions.'
  ),
  (
    'cfg_PAE002',
    'config',
    'PRICE_ACTION_EVENT_LAYER_POLICY',
    'text',
    'layer_04_event_overlay_event_not_new_model_layer;feeds_layer_03_04_05_as_evidence;post_event_realization_is_label_only;no_action_or_execution_output',
    'trading-model/docs/05_layer_04_event_overlay.md',
    'price_action;false_breakout;event_overlay_model;target_context_state;alpha_confidence_model',
    'sync_artifact',
    'Policy for false-breakout style price-action evidence: represent it as Layer 4 event-overlay evidence and optional Layer 3/5 consumable context, without adding a ninth model layer or emitting action/execution fields.'
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
