-- Register EventRiskGovernor event-family threshold/grading queue builder.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGTH001',
  'script',
  'MODEL_08_EVENT_FAMILY_THRESHOLD_GRADING_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_threshold_grading.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_threshold_grading.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_threshold_grading.py',
  'event_family_threshold_grading_v1;event_family_threshold_grading_summary_v1;model_08_event_risk_governor;event_family_threshold_queue',
  'sync_artifact',
  'Builds the EventRiskGovernor event-family threshold/grading queue. It removes measured no-clear families from the active threshold queue while preserving audit artifacts, keeps accepted risk/control seeds and expanded screening candidates, and performs no provider calls, model training, activation, broker/account mutation, destructive SQL, or artifact deletion.'
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
