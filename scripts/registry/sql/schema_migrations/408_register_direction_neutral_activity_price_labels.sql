-- Register direction-neutral activity-price proof labels.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_APDN001',
    'config',
    'ACTIVITY_PRICE_PROOF_PRIMARY_METRIC_POLICY',
    'text',
    'direction_neutral_tradability_first',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;activity_price_relationship_proof_gate;event_activity_bridge;model_promotion',
    'sync_artifact',
    'Primary proof must evaluate absolute movement and tradeable path expansion because downside paths are tradable. Signed average forward return is secondary.'
  ),
  (
    'cfg_APDN002',
    'config',
    'ACTIVITY_PRICE_DIRECTION_NEUTRAL_LABELS',
    'text',
    'absolute_forward_return;forward_path_range;max_favorable_excursion;max_adverse_excursion;tradeable_excursion;forward_volatility_expansion;forward_gap_or_jump_abs;path_asymmetry',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;training_labels;direction_neutral_tradability;abnormal_activity',
    'sync_artifact',
    'Direction-neutral label families for the first activity-price proof gate.'
  ),
  (
    'cfg_APDN003',
    'config',
    'ACTIVITY_PRICE_SECONDARY_DIRECTIONAL_LABELS',
    'text',
    'signed_forward_return;forward_drawdown;forward_reversal;close_to_close_continuation;open_gap_followthrough;intraday_absorption_score',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;training_labels;directional_classification;abnormal_activity',
    'sync_artifact',
    'Secondary directional labels used after direction-neutral tradability is established.'
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
