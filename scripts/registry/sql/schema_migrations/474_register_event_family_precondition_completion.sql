-- Register safe local all-family event precondition packet builder.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGPRC001',
  'script',
  'MODEL_08_EVENT_FAMILY_PRECONDITION_COMPLETION_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_precondition_completion.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_precondition_completion.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_precondition_completion.py',
  'event_family_precondition_completion_v1;event_family_scouting_packet_v1;event_family_precondition_completion_summary_v1;model_08_event_risk_governor;fine_grained_event_family_association',
  'sync_artifact',
  'Builds all-family EventRiskGovernor precondition packets before final association judgment. It emits one maintained event_family_scouting_packet_v1 for each of 29 fine-grained families, defining source precedence, point-in-time clocks, baselines, matched controls, label windows, residual requirements, liquidity requirements, and early-stop gates. It fills the missing-packet governance gap but performs no provider calls, training, activation, broker/account mutation, destructive SQL, artifact deletion, or final alpha/risk promotion.'
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
