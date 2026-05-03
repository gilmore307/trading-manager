-- Register the Layer 1 model explainability and diagnostics artifact names.
INSERT INTO trading_registry (
  id,
  kind,
  key,
  payload_format,
  payload,
  path,
  applies_to,
  artifact_sync_policy,
  note
) VALUES
  (
    'trm_MRMEXPL',
    'term',
    'MODEL_01_MARKET_REGIME_EXPLAINABILITY',
    'text',
    'model_01_market_regime_explainability',
    'trading-model/docs/91_layer_01_market_regime.md',
    'trading-model;market_regime_model;model_01_market_regime',
    'registry_only',
    'Accepted Layer 1 MarketRegimeModel explainability artifact/table name. Owns human-review detail such as factor attribution, source feature contributions, bucket-level scores, evidence-role references, config/factor-spec references, and accepted reason-code detail; downstream layers should not hard-depend on this artifact.'
  ),
  (
    'trm_MRMDIAG',
    'term',
    'MODEL_01_MARKET_REGIME_DIAGNOSTICS',
    'text',
    'model_01_market_regime_diagnostics',
    'trading-model/docs/91_layer_01_market_regime.md',
    'trading-model;market_regime_model;model_01_market_regime',
    'registry_only',
    'Accepted Layer 1 MarketRegimeModel diagnostics artifact/table name. Owns acceptance, monitoring, and gating evidence such as freshness, missingness, minimum-history, standardization, feature coverage, stability, baseline comparison, downstream usefulness, and no-future-leak checks.'
  );
