-- Align the shared market_context_state term with the finalized Layer 1 V2.2 output contract.

UPDATE trading_registry
SET note = 'Conceptual Layer 1 downstream state wrapping the current MarketRegimeModel V2.2 direction-neutral market-context scores. It is conditioning context only, not sector/ETF/stock ranking, strategy choice, option contract choice, position sizing, or final action.',
    path = 'trading-model/docs/02_layer_01_market_regime.md',
    applies_to = 'trading-model;market_regime_model;model_01_market_regime;direction_neutral_tradability',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MARKET_CONTEXT_STATE';
