-- Register stable model evaluation and promotion-review entrypoints used by
-- promotion governance. These are callable operational scripts, not ordinary
-- implementation source files.
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
    'scr_MRMEVAL1',
    'script',
    'MODEL_01_MARKET_REGIME_EVALUATE_PROMOTION_EVIDENCE',
    'command',
    'python3 scripts/models/model_01_market_regime/evaluate_model_01_market_regime.py',
    '/root/projects/trading-model/scripts/models/model_01_market_regime/evaluate_model_01_market_regime.py',
    'trading-model;market_regime_model;model_01_market_regime;model_evaluation;model_promotion',
    'sync_artifact',
    'Stable callable entrypoint for MarketRegimeModel evaluation and promotion evidence generation. Default path is fixture/local dry-run; --from-database is read-only and produces real-data promotion evidence without writing governance rows.'
  ),
  (
    'scr_MRMREVIEW',
    'script',
    'MODEL_01_MARKET_REGIME_REVIEW_PROMOTION',
    'command',
    'python3 scripts/models/model_01_market_regime/review_market_regime_promotion.py',
    '/root/projects/trading-model/scripts/models/model_01_market_regime/review_market_regime_promotion.py',
    'trading-model;market_regime_model;model_01_market_regime;model_promotion;promotion_review',
    'sync_artifact',
    'Stable callable entrypoint for MarketRegimeModel promotion review. Review-only by default; reviewed decisions may be persisted with --write-decision and accepted approvals may activate a config only with --activate-approved-config.'
  ),
  (
    'scr_SCMEVAL1',
    'script',
    'MODEL_02_SECTOR_CONTEXT_EVALUATE_PROMOTION_EVIDENCE',
    'command',
    'python3 scripts/models/model_02_sector_context/evaluate_model_02_sector_context.py',
    '/root/projects/trading-model/scripts/models/model_02_sector_context/evaluate_model_02_sector_context.py',
    'trading-model;sector_context_model;model_02_sector_context;model_evaluation;model_promotion',
    'sync_artifact',
    'Stable callable entrypoint for SectorContextModel evaluation and promotion evidence generation. Default path is fixture/local dry-run; --from-database is read-only and produces real-data promotion evidence without writing governance rows.'
  ),
  (
    'scr_SCMREVIEW',
    'script',
    'MODEL_02_SECTOR_CONTEXT_REVIEW_PROMOTION',
    'command',
    'python3 scripts/models/model_02_sector_context/review_sector_context_promotion.py',
    '/root/projects/trading-model/scripts/models/model_02_sector_context/review_sector_context_promotion.py',
    'trading-model;sector_context_model;model_02_sector_context;model_promotion;promotion_review',
    'sync_artifact',
    'Stable callable entrypoint for SectorContextModel promotion review. Review-only by default; local fallback is conservative and defers fixture/dry-run evidence; reviewed decisions may be persisted with --write-decision.'
  )
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = CURRENT_TIMESTAMP;
