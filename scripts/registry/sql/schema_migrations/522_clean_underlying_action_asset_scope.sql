-- Clean remaining Layer 7 direct-underlying vocabulary to include crypto/direct-underlying-only routes.

UPDATE trading_registry
SET note = 'Layer 7 boundary policy: UnderlyingActionModel produces an offline direct underlying/spot action thesis for stock, ETF, or crypto-style candidates, with optional Layer 8 trading-guidance handoff. It must not place broker/exchange orders, emit broker order fields, choose option contracts, or mutate broker/account state.',
    updated_at = NOW()
WHERE id = 'cfg_UAPB001'
  AND key = 'UNDERLYING_ACTION_BOUNDARY_POLICY';

UPDATE trading_registry
SET note = 'Point-in-time current direct-underlying/spot position state input. It describes current stock, ETF, or crypto-style exposure state for action planning; it is not an order or execution record.',
    updated_at = NOW()
WHERE id = 'trm_CUPS01'
  AND key = 'CURRENT_UNDERLYING_POSITION_STATE';
