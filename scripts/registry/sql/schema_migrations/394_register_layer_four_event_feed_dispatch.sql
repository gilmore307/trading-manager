-- Register bounded manager dispatch surface for Layer 4 event-feed backfill artifacts.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_L4EVTDIS001',
    'script',
    'MANAGER_DISPATCH_LAYER_FOUR_EVENT_FEED_BACKFILL',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/dispatch_event_feed_backfill.py',
    'trading-manager/scripts/tasks/dispatch_event_feed_backfill.py;trading-manager/src/trading_manager_tasks/event_feed_dispatch.py',
    'layer_04_event_overlay;event_source_coverage;alpaca_news;gdelt_news;trading_economics_calendar_web;sec_company_financials',
    'sync_artifact',
    'Validates or explicitly dispatches bounded Layer 4 event-feed provider acquisition from prepared task keys. Provider calls require --execute-provider-calls; model activation, broker execution, account mutation, and dashboard read-model writes remain forbidden.'
  ),
  (
    'term_L4EVTDIS001',
    'term',
    'LAYER_FOUR_EVENT_FEED_BACKFILL_DISPATCH',
    'text',
    'layer_four_event_feed_backfill_dispatch',
    'trading-manager/src/trading_manager_tasks/event_feed_dispatch.py;trading-manager/docs/81_decision.md',
    'historical_modeling;source_04_event_overlay;event_feed_artifacts;provider_acquisition',
    'sync_artifact',
    'Manager-owned bounded dispatch surface for the reviewed event-feed task keys consumed by source_04_event_overlay event_artifact_paths.'
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
