-- Register final current-cycle EventRiskGovernor judgment builder.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGFJ001',
  'script',
  'MODEL_08_EVENT_LAYER_FINAL_JUDGMENT_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_layer_final_judgment.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_layer_final_judgment.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_layer_final_judgment.py',
  'event_layer_final_judgment_v1;event_layer_final_judgment_summary_v1;model_08_event_risk_governor;event_risk_governor_final_posture',
  'sync_artifact',
  'Builds the final current-cycle EventRiskGovernor posture judgment from reviewed local evidence. The accepted posture is a bounded EventRiskGovernor/EventIntelligenceOverlay, not a standalone event-alpha model. It permits only risk/control outputs from current evidence, accepts CPI surprise and earnings scheduled shells for risk/control only, accepts zero standalone directional-alpha event families, and performs no provider calls, training, activation, broker/account mutation, destructive SQL, or artifact deletion.'
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
