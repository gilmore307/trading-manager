-- Register unified review decision artifact builder.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MPR001',
    'artifact_type',
    'REVIEW_DECISION_ARTIFACT',
    'text',
    'review_decision_v1',
    'trading-manager/docs/96_model_promotion.md',
    'review_decision_v1;model_promotion_review_v1;promotion_control_plane;activation_record_v1',
    'sync_artifact',
    'Generic manager review decision artifact. Deferred, rejected, failed, partial, revoked, or superseded decisions cannot activate configs; activation requires an approving review_decision_v1.'
  ),
  (
    'art_MPR002',
    'artifact_type',
    'ACTIVATION_RECORD_ARTIFACT',
    'text',
    'activation_record_v1',
    'trading-manager/docs/96_model_promotion.md',
    'activation_record_v1;approved_review_decision;promotion_control_plane;rollback_ref',
    'sync_artifact',
    'Generic manager activation record artifact. It records approved config activation and rollback refs only; it does not execute broker or exchange actions.'
  ),
  (
    'scr_MPR002',
    'script',
    'MANAGER_REVIEW_DECISION_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/build_review_decision.py',
    '/root/projects/trading-manager/scripts/tasks/build_review_decision.py',
    'review_decision_v1;model_promotion_review_v1;promotion_control_plane',
    'sync_artifact',
    'Build generic review_decision_v1 artifacts without approving activation unless a separate approved decision is explicitly used to build activation_record_v1.'
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
