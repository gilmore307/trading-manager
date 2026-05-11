-- Register script-called agent model-promotion decision helper after owner-observed automation policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_MODELPROMO002',
  'script',
  'BUILD_AGENT_MODEL_PROMOTION_DECISION',
  'command',
  'PYTHONPATH=src python3 scripts/tasks/build_agent_model_promotion_decision.py --promotion-request-ref ${PROMOTION_REQUEST_REF} --decision-status ${DECISION_STATUS} --decision-reason ${DECISION_REASON}',
  '/root/projects/trading-manager/scripts/tasks/build_agent_model_promotion_decision.py',
  'agent_model_promotion_decision_v1;model_promotion_review_v1;activation_record_v1;owner_observed_agent_decision',
  'sync_artifact',
  'Builds the script-called owner-observed agent decision artifact required before production model activation. It has no activation side effects.'
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
