-- Register event lifecycle timing contract for Layer 8 event-risk governance.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_ELC001',
    'term',
    'EVENT_LIFECYCLE_CONTRACT',
    'text',
    'event_lifecycle_contract',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_risk_governor;event_interpretation_v1;source_04_event_overlay;trading-manager;trading-data;trading-model',
    'sync_artifact',
    'Contract requiring event intelligence to preserve lifecycle class and clocks so scheduled-known catalysts are not trained or evaluated as unscheduled surprise events.'
  ),
  (
    'cfg_ELTV001',
    'config',
    'EVENT_LIFECYCLE_TYPE_VALUES',
    'text',
    'scheduled_known_outcome_later;unscheduled_surprise;scheduled_recurring_data_release;multi_stage_developing_event;unknown',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_lifecycle_contract;event_risk_governor;event_interpretation_v1;source_04_event_overlay',
    'sync_artifact',
    'Accepted event lifecycle classes. Scheduled-known catalysts may be visible before outcome release; surprise events cannot have a specific pre-event event row.'
  ),
  (
    'cfg_ELCV001',
    'config',
    'EVENT_LIFECYCLE_CLOCK_FIELDS',
    'text',
    'event_awareness_time;event_scheduled_time;event_effective_time;event_actual_time;source_published_time;source_updated_time;ingested_time;available_time;interpretation_time;resolution_time;decision_time;tradeable_time;reaction_window',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_lifecycle_contract;point_in_time;event_interpretation_v1;source_04_event_overlay;event_risk_governor',
    'sync_artifact',
    'Lifecycle clocks that preserve awareness, scheduled release, source publication, system availability, interpretation, resolution, decision/tradeability, and evaluation-only reaction windows.'
  ),
  (
    'cfg_ELS001',
    'config',
    'EVENT_LIFECYCLE_STATE_VALUES',
    'text',
    'scheduled_future;pre_event_window;live_release_window;post_event_initial_reaction;post_event_decay;developing_update;resolved;stale_event;unknown',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_lifecycle_contract;event_risk_governor;event_interpretation_v1',
    'sync_artifact',
    'Recommended state values describing where the current point-in-time event row sits in the event arc.'
  ),
  (
    'cfg_ELG001',
    'config',
    'EVENT_LIFECYCLE_GOLDEN_EXAMPLES',
    'text',
    'earnings=scheduled_known_outcome_later;cpi_macro_release=scheduled_recurring_data_release;surprise_regulatory_raid_or_news=unscheduled_surprise',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_lifecycle_contract;event_family_training;golden_tests;event_risk_governor',
    'sync_artifact',
    'Initial golden lifecycle examples for event-family contract tests: earnings, CPI/macro release, and unscheduled surprise regulatory/news events.'
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
