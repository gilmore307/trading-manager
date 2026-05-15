-- Register Layer 4 event-source coverage gate and downstream invalidation helper.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_L4EVTCOV001',
    'term',
    'LAYER_FOUR_EVENT_SOURCE_COVERAGE_GATE',
    'text',
    'layer_four_event_source_coverage_gate',
    'trading-manager/src/trading_manager_tasks/layer_four_event_overlay.py;trading-data/src/data_source/source_04_event_overlay/feed_event_extraction.py;trading-manager/docs/81_decision.md',
    'layer_04_event_overlay;source_04_event_overlay;historical_modeling;event_source_coverage',
    'sync_artifact',
    'Layer 4 write-mode materialization must have reviewed local artifacts for Alpaca news, GDELT news, SEC company financials, and Trading Economics calendar rows before downstream Layer 4+ model stages may advance.'
  ),
  (
    'scr_L4EVTINV001',
    'script',
    'MANAGER_INVALIDATE_LAYER_FOUR_DOWNSTREAM_OUTPUTS',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/invalidate_layer_four_downstream_outputs.py',
    'trading-manager/scripts/tasks/invalidate_layer_four_downstream_outputs.py;trading-manager/src/trading_manager_tasks/model_training_invalidation.py',
    'historical_modeling;layer_04_event_overlay;layer_05_alpha_confidence;layer_06_position_projection;layer_07_underlying_action;layer_08_option_expression;stale_output_invalidation',
    'sync_artifact',
    'State-only helper that marks stale Layer 4+ workflow stages rebuild-required after event-source contract repair. It does not delete artifacts, call providers, activate models, submit broker orders, mutate accounts, or write dashboard read models.'
  ),
  (
    'cfg_L4EVTCOV001',
    'config',
    'LAYER_FOUR_REQUIRED_EVENT_FEED_ARTIFACTS',
    'text',
    'alpaca_news:equity_news.csv;gdelt_news:gdelt_article.csv;sec_company_financials:sec_company_fact.csv;trading_economics_calendar_web:trading_economics_calendar_event.csv',
    'trading-manager/src/trading_manager_tasks/layer_four_event_overlay.py;trading-data/src/data_source/source_04_event_overlay/README.md',
    'source_04_event_overlay;event_artifact_paths;event_feed_coverage',
    'sync_artifact',
    'Required reviewed saved feed artifacts for a complete Layer 4 event-overlay rebuild. Missing artifacts block write-mode materialization.'
  ),
  (
    'fld_L4EVTCOV001',
    'field',
    'EVENT_ARTIFACT_PATHS',
    'field_name',
    'event_artifact_paths',
    'trading-data/src/data_source/source_04_event_overlay/README.md;trading-data/src/data_source/source_04_event_overlay/pipeline.py',
    'source_04_event_overlay;event_overlay_model;local_feed_artifact_extraction',
    'sync_artifact',
    'Task-key list of reviewed local saved feed artifacts that source_04_event_overlay normalizes into canonical event overview rows without provider calls.'
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
