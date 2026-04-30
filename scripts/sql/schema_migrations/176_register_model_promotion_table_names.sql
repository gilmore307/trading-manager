INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_MDPROM001',
    'term',
    'MODEL_CONFIG_VERSION_TABLE',
    'text',
    'model_config_version',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_promotion;model_config_version',
    'registry_only',
    'Accepted generic trading_model governance table name for model configuration versions. Config versions are evidence inputs for promotion candidates; concrete columns are intentionally not registered yet.'
  ),
  (
    'trm_MDPROM002',
    'term',
    'MODEL_PROMOTION_CANDIDATE_TABLE',
    'text',
    'model_promotion_candidate',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_promotion;model_evaluation',
    'registry_only',
    'Accepted generic trading_model governance table name for promotion candidates. Candidates must reference an evaluation run and a model config version before any decision can be recorded; concrete columns are intentionally not registered yet.'
  ),
  (
    'trm_MDPROM003',
    'term',
    'MODEL_PROMOTION_DECISION_TABLE',
    'text',
    'model_promotion_decision',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_promotion',
    'registry_only',
    'Accepted generic trading_model governance table name for approve, reject, defer, or related promotion decisions. Concrete columns are intentionally not registered yet.'
  ),
  (
    'trm_MDPROM004',
    'term',
    'MODEL_PROMOTION_ROLLBACK_TABLE',
    'text',
    'model_promotion_rollback',
    'trading-model/docs/05_decision.md',
    'trading-model;model_governance;model_promotion;model_rollback',
    'registry_only',
    'Accepted generic trading_model governance table name for rollback requests away from a promoted model configuration. Concrete columns are intentionally not registered yet.'
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
