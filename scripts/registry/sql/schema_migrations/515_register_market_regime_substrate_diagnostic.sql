-- Register the read-only Layer 1 substrate diagnostic entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_MRMDIAG1',
  'script',
  'MODEL_01_MARKET_REGIME_DIAGNOSE_SUBSTRATE',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_01_market_regime/diagnose_model_01_market_regime_substrate.py',
  '/root/projects/trading-model/scripts/models/model_01_market_regime/diagnose_model_01_market_regime_substrate.py;/root/projects/trading-model/src/models/model_01_market_regime/substrate_diagnostics.py',
  'trading-model;market_regime_model;model_01_market_regime;feature_01_market_regime;source_01_market_regime;model_promotion;promotion_readiness;substrate_diagnostic',
  'sync_artifact',
  'Stable callable read-only diagnostic for Layer 1 MarketRegimeModel promotion substrate gaps. It separates source-bar sparsity, feature signal/lookback coverage, and feature-to-model alignment; --from-database reads source/feature/model tables and writes no source, feature, model, evaluation, promotion, activation, broker, or account rows.'
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
