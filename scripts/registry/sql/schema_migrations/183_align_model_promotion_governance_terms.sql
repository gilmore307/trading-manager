UPDATE trading_registry
SET
    key = 'MODEL_PROMOTION_METRIC_TABLE',
    payload = 'model_promotion_metric',
    applies_to = 'trading-model;model_governance;model_evaluation;model_promotion',
    note = 'Accepted generic trading_model governance table name for promotion evidence metrics across model layers, factors, targets, horizons, and dataset splits. Concrete columns are intentionally not registered yet.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'trm_MDGOV006';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_MDPROM005',
    'term',
    'MODEL_PROMOTION_ACTIVATION_TABLE',
    'text',
    'model_promotion_activation',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_promotion;model_activation',
    'registry_only',
    'Accepted generic trading_model governance table name for immutable activation events that record actual model configuration replacement after an accepted promotion decision. Concrete columns are intentionally not registered yet.'
  )
ON CONFLICT (id) DO UPDATE SET
    kind = excluded.kind,
    key = excluded.key,
    payload_format = excluded.payload_format,
    payload = excluded.payload,
    path = excluded.path,
    applies_to = excluded.applies_to,
    artifact_sync_policy = excluded.artifact_sync_policy,
    note = excluded.note,
    updated_at = CURRENT_TIMESTAMP;
