-- Register safe local CPI/inflation event-control association readiness entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGCPI001',
  'script',
  'MODEL_08_CPI_INFLATION_ASSOCIATION_READINESS_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_cpi_inflation_association_readiness.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_cpi_inflation_association_readiness.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/cpi_inflation_association_readiness.py',
  'cpi_inflation_association_readiness_v1;cpi_inflation_release;event_control_comparison;model_08_event_risk_governor;fine_grained_event_family_association',
  'sync_artifact',
  'Builds the safe local CPI/inflation association-control readiness slice. It scans existing local calendar and ETF bar artifacts, emits CPI event labels, same-month control labels, and event/control comparisons, but keeps the family underpowered until enough local event months, official-source canonicalization, market/sector/target-state controls, and accepted surprise definitions exist. It performs no provider calls, model activation, broker/account mutation, or artifact deletion.'
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
