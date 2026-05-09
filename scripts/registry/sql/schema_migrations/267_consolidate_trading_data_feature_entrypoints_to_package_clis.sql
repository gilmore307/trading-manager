-- Consolidate trading-data feature generation registry rows on package CLI entrypoints.
-- The importable implementations remain in src/data_feature/; duplicate scripts/generate_feature_*.py wrappers are intentionally removed.

UPDATE trading_registry
SET payload = 'trading-data-feature-01-market-regime',
    path = '/root/projects/trading-data/src/data_feature/feature_01_market_regime/__main__.py',
    note = 'Stable package CLI entrypoint for generating Layer 1 MarketRegimeModel deterministic feature rows from accepted source_01_market_regime evidence. The importable implementation lives under src/data_feature/feature_01_market_regime.',
    updated_at = NOW()
WHERE id = 'scr_F1MRGEN'
  AND kind = 'script'
  AND key = 'FEATURE_01_MARKET_REGIME_GENERATE';

UPDATE trading_registry
SET payload = 'trading-data-feature-02-sector-context',
    path = '/root/projects/trading-data/src/data_feature/feature_02_sector_context/__main__.py',
    note = 'Stable package CLI entrypoint for generating Layer 2 SectorContextModel deterministic feature rows. The importable implementation lives under src/data_feature/feature_02_sector_context.',
    updated_at = NOW()
WHERE id = 'scr_F2SCGEN'
  AND kind = 'script'
  AND key = 'FEATURE_02_SECTOR_CONTEXT_GENERATE';

UPDATE trading_registry
SET payload = 'trading-data-feature-03-target-state-vector',
    path = '/root/projects/trading-data/src/data_feature/feature_03_target_state_vector/__main__.py',
    note = 'Stable package CLI entrypoint for reading source_03_target_state plus optional Layer 1/2 context rows and writing feature_03_target_state_vector JSONB market/sector/target/cross-state blocks. The importable implementation lives under src/data_feature/feature_03_target_state_vector.',
    updated_at = NOW()
WHERE id = 'scr_F3TSVGEN'
  AND kind = 'script'
  AND key = 'FEATURE_03_TARGET_STATE_VECTOR_GENERATE';

UPDATE trading_registry
SET payload = 'trading-data-feature-04-event-overlay',
    path = '/root/projects/trading-data/src/data_feature/feature_04_event_overlay/__main__.py',
    note = 'Stable package CLI entrypoint for reading source_04_event_overlay rows and writing feature_04_event_overlay JSONB event overview feature blocks. The importable implementation lives under src/data_feature/feature_04_event_overlay.',
    updated_at = NOW()
WHERE id = 'scr_F4EOGEN'
  AND kind = 'script'
  AND key = 'FEATURE_04_EVENT_OVERLAY_GENERATE';

UPDATE trading_registry
SET payload = 'trading-data-feature-08-option-expression',
    path = '/root/projects/trading-data/src/data_feature/feature_08_option_expression/__main__.py',
    note = 'Stable package CLI entrypoint for reading source_05_option_expression rows and writing feature_08_option_expression JSONB option-candidate feature blocks. The importable implementation lives under src/data_feature/feature_08_option_expression.',
    updated_at = NOW()
WHERE id = 'scr_F8OEGEN'
  AND kind = 'script'
  AND key = 'FEATURE_08_OPTION_EXPRESSION_GENERATE';
