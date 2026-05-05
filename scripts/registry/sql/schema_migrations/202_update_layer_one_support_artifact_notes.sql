-- Align Layer 1 support-artifact registry notes with the V2.2 state-score output contract.

UPDATE trading_registry
SET note = 'Accepted Layer 1 MarketRegimeModel explainability artifact/table name. Owns human-review detail such as state-score attribution, source signal-group contributions, bucket-level scores, evidence-role references, config/spec references, and accepted reason-code detail; downstream layers should not hard-depend on this artifact.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MODEL_01_MARKET_REGIME_EXPLAINABILITY';
