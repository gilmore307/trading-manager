-- Register event-model closeout and safe regeneration planning entrypoints.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_M8ERGCLS001',
    'script',
    'MODEL_08_EVENT_RISK_GOVERNOR_CLOSEOUT_REPORT_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_model_closeout_report.py',
    '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_model_closeout_report.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_model_closeout.py',
    'event_model_closeout_report_v1;model_08_event_risk_governor;event_risk_governor;event_family_scouting;storage_lifecycle_hold',
    'sync_artifact',
    'Builds the accepted event-model closeout report: Layer 8 remains a bounded EventRiskGovernor / EventIntelligenceOverlay, broad event alpha and signed earnings/guidance alpha remain blocked, diagnostic artifacts are preserved, and storage deletion stays on hold until reviewed regeneration completes.'
  ),
  (
    'scr_L8ERGREG001',
    'script',
    'MANAGER_PLAN_EVENT_MODEL_REGENERATION',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/plan_event_model_regeneration.py --start-month ${START_MONTH} --end-month ${END_MONTH}',
    '/root/projects/trading-manager/scripts/tasks/plan_event_model_regeneration.py;/root/projects/trading-manager/src/trading_manager_tasks/event_model_regeneration_plan.py',
    'manager_event_model_regeneration_plan_v1;layer_08_event_risk_governor;source_08_event_risk_governor;feature_08_event_risk_governor;model_08_event_risk_governor;storage_lifecycle_hold',
    'sync_artifact',
    'Builds the non-mutating EventRiskGovernor regeneration plan: preserve persistent Layer 1/2 data and valid base Layer 3-7 outputs, supersede old event-overlay or abnormal-activity-only Layer 8 artifacts, rebuild Layer 8 only after reviewed event-feed coverage, and keep deletion dry-run-only until reviewed closeout.'
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
