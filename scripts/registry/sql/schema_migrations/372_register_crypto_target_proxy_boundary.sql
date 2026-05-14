-- Register the accepted boundary that single-asset crypto ETFs are target proxies,
-- not Layer 1/2 market/sector context rows by default.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_CTP001',
    'term',
    'CRYPTO_SINGLE_ASSET_ETF_TARGET_PROXY_BOUNDARY',
    'text',
    'ibit_etha_fsol_target_proxy_only;bitw_layer_01_broad_crypto_market_state;bkch_layer_02_crypto_sector_context',
    'trading-storage/docs/81_decision.md;trading-storage/main/shared/market_regime_etf_universe.csv;trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
    'market_regime_etf_universe;market_regime_relative_strength_combinations;crypto_target_proxy;layer_01_market_regime;layer_02_sector_context;layer_03_plus_target_study',
    'sync_artifact',
    'Accepted boundary: single-asset crypto ETFs such as IBIT, ETHA, and FSOL are not default Layer 1/2 context rows. Use BITW for broad Layer 1 crypto-basket market state, BKCH for Layer 2 blockchain/crypto-related equity sector context, and single-asset ETFs only as auxiliary target/proxy instruments when studying BTC/ETH/SOL-like targets.'
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

UPDATE trading_registry
SET note = 'Shared curated ETF universe for Layer 1 market-state instruments and Layer 2 sector/industry/theme observation instruments. The model_layer column is the authoritative Layer 1/Layer 2 scope discriminator; universe_type remains descriptive row classification. Single-asset crypto ETFs such as IBIT, ETHA, and FSOL are target/proxy instruments by default and are intentionally excluded from this Layer 1/2 context universe.',
    updated_at = NOW()
WHERE id = 'out_MKTETFUNI';

UPDATE trading_registry
SET note = 'Shared curated relative-strength combination table for market-context feature generation. The model_layer column is the authoritative Layer 1/Layer 2 scope discriminator; Layer 1 consumes layer_01_market_regime rows and Layer 2 consumes layer_02_sector_context rows. Single-asset crypto ETF proxy pairs are excluded by default; use them only inside target-specific crypto studies.',
    updated_at = NOW()
WHERE id = 'out_MRRS001';
