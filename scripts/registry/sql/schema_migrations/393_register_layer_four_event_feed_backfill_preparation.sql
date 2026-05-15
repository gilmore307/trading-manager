-- Register manager preparation entrypoint for Layer 4 event-feed backfill task keys.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_L4EVTBF001',
    'script',
    'MANAGER_PREPARE_LAYER_FOUR_EVENT_FEED_BACKFILL',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/prepare_layer_four_event_feed_backfill.py',
    'trading-manager/scripts/tasks/prepare_layer_four_event_feed_backfill.py;trading-manager/src/trading_manager_tasks/event_feed_backfill.py',
    'layer_04_event_overlay;event_source_coverage;alpaca_news;gdelt_news;trading_economics_calendar_web;sec_company_financials',
    'sync_artifact',
    'Prepares reviewed monthly event-feed task keys required before rebuilding Layer 4+ outputs. Preparation performs no provider calls, model activation, broker execution, account mutation, or dashboard read-model writes.'
  ),
  (
    'term_L4EVTBF001',
    'term',
    'LAYER_FOUR_EVENT_FEED_BACKFILL_PREPARATION',
    'text',
    'layer_four_event_feed_backfill_preparation',
    'trading-manager/src/trading_manager_tasks/event_feed_backfill.py;trading-manager/docs/81_decision.md',
    'historical_modeling;source_04_event_overlay;event_feed_artifacts',
    'sync_artifact',
    'Manager-owned preparation surface for the monthly event-feed artifacts consumed by source_04_event_overlay event_artifact_paths.'
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
