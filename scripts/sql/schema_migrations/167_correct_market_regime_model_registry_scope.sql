-- Correct migration 166 after registry tests confirmed active data_kind rows
-- must remain empty and available_time is already registered under an older
-- row id. Keep the model name as shared terminology and keep factor fields.

UPDATE trading_registry
SET
    kind = 'term',
    key = 'MODEL_01_MARKET_REGIME',
    payload_format = 'text',
    payload = 'model_01_market_regime',
    path = 'trading-model/docs/07_system_model_architecture_rfc.md',
    applies_to = 'trading-model;trading-derived;market_regime_model;derived_01_market_regime',
    artifact_sync_policy = 'registry_only',
    note = 'Accepted Layer 1 MarketRegimeModel V1 model-output term for the continuous market-state vector written to trading_model.model_01_market_regime. V1 does not require clustering, hard state ids, state probabilities, or human-readable regime labels.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'dki_MRMV001';

DELETE FROM trading_registry
WHERE id = 'fld_MRM001';
