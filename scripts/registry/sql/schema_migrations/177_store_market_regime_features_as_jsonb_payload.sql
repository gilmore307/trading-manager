UPDATE trading_registry
SET note = 'Layer 1 MarketRegimeModel deterministic feature-output boundary. Each row is one point-in-time market-regime feature snapshot keyed by snapshot_time; generated feature values are stored as model-local keys in feature_payload_json JSONB to avoid PostgreSQL row-size limits. Concrete generated feature keys such as spy_return_30m remain governed by reviewed feature-family rules/catalogs and are not individually registered as registry rows.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'FEATURE_01_MARKET_REGIME';
