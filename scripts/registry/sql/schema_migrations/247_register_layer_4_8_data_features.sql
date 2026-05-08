-- Register deterministic trading-data feature surfaces for Layers 4 and 8.
-- These are real source-derived feature packages, not fake layer symmetry:
-- Layer 4 prepares event-overview feature payloads for EventOverlayModel, and
-- Layer 8 prepares option-candidate feature payloads for OptionExpressionModel.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'dki_EOFS001',
    'data_feature',
    'FEATURE_04_EVENT_OVERLAY',
    'text',
    'feature_04_event_overlay',
    'trading-data/src/data_feature/feature_04_event_overlay',
    'trading-data;trading-model;source_04_event_overlay;event_overlay_model;model_04_event_overlay;event_context_vector',
    'sync_artifact',
    'Layer 4 deterministic event-overlay feature surface. trading-data derives point-in-time event-category, scope, dedup, source-priority, and quality payloads from accepted source_04_event_overlay rows; trading-model owns final event_context_vector construction.'
  ),
  (
    'dki_OEFS001',
    'data_feature',
    'FEATURE_08_OPTION_EXPRESSION',
    'text',
    'feature_08_option_expression',
    'trading-data/src/data_feature/feature_08_option_expression',
    'trading-data;trading-model;source_05_option_expression;option_expression_model;model_08_option_expression;option_expression_plan',
    'sync_artifact',
    'Layer 8 deterministic option-expression candidate feature surface. trading-data derives point-in-time moneyness, spread/liquidity, IV, Greeks, and quality payloads from accepted source_05_option_expression rows; trading-model owns contract ranking and expression choice.'
  ),
  (
    'scr_F4EOGEN',
    'script',
    'FEATURE_04_EVENT_OVERLAY_GENERATE',
    'command',
    'trading-data-feature-04-event-overlay',
    '/root/projects/trading-data/src/data_feature/feature_04_event_overlay/__main__.py',
    'trading-data;source_04_event_overlay;feature_04_event_overlay;event_overlay_model;model_04_event_overlay',
    'sync_artifact',
    'Stable callable entrypoint for reading source_04_event_overlay rows and writing feature_04_event_overlay JSONB event overview feature blocks.'
  ),
  (
    'scr_F8OEGEN',
    'script',
    'FEATURE_08_OPTION_EXPRESSION_GENERATE',
    'command',
    'trading-data-feature-08-option-expression',
    '/root/projects/trading-data/src/data_feature/feature_08_option_expression/__main__.py',
    'trading-data;source_05_option_expression;feature_08_option_expression;option_expression_model;model_08_option_expression',
    'sync_artifact',
    'Stable callable entrypoint for reading source_05_option_expression rows and writing feature_08_option_expression JSONB option-candidate feature blocks.'
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
  updated_at = NOW();
