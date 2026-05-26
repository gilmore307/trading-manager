-- Remove remaining stale current-registry rows discovered by the full
-- registry review. Compatibility policy rows remain when they describe an
-- active read-compat boundary; legacy diagnostic task rows are not active
-- registry surfaces.

UPDATE trading_registry
SET key = 'PROMOTION_REPLAY_WINDOW_POLICY',
    updated_at = NOW()
WHERE key = 'PROMOTION_REPLAY_REPLAY_WINDOW_POLICY';

DELETE FROM trading_registry
WHERE key IN (
  'MANAGER_MATERIALIZE_LAYER_TEN_EVENT_RISK_INPUTS',
  'MANAGER_LAYER_TEN_EVENT_RISK_INPUT_MATERIALIZATION'
);
