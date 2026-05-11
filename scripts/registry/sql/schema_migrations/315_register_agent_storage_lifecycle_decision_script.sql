-- Register script-called agent storage-lifecycle decision helper.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_STORLIFE002',
  'script',
  'BUILD_AGENT_STORAGE_LIFECYCLE_DECISION',
  'command',
  'PYTHONPATH=src python3 scripts/tasks/build_agent_storage_lifecycle_decision.py --storage-lifecycle-request-ref ${STORAGE_LIFECYCLE_REQUEST_REF} --decision-status ${DECISION_STATUS} --decision-reason ${DECISION_REASON}',
  '/root/projects/trading-manager/scripts/tasks/build_agent_storage_lifecycle_decision.py',
  'agent_storage_lifecycle_decision_v1;storage_lifecycle_request_v1;storage_lifecycle;owner_observed_agent_decision',
  'sync_artifact',
  'Builds the script-called owner-observed agent decision artifact required before storage lifecycle mutation. It has no storage mutation side effects.'
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
