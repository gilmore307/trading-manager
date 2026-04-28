-- Fold the equity_abnormal_activity detector into the event overlay bundle boundary.
-- It remains implementation code and a final data_kind output shape, but it is not
-- a separate manager-facing registry data_bundle.

DELETE FROM trading_registry
WHERE kind = 'data_bundle'
  AND key = 'EQUITY_ABNORMAL_ACTIVITY_BUNDLE';

DELETE FROM trading_registry
WHERE kind = 'config'
  AND key = 'EQUITY_ABNORMAL_ACTIVITY_BUNDLE_CONFIG';

UPDATE trading_registry
SET
  applies_to = '06_event_overlay_model_inputs;alpaca_bars;alpaca_liquidity;event_database',
  note = 'Derived event-style row for abnormal stock/ETF price, volume, relative-strength, gap, or liquidity activity feeding EventOverlayModel. Produced by the event overlay detector path, not a standalone manager-facing bundle.'
WHERE kind = 'data_kind'
  AND key = 'EQUITY_ABNORMAL_ACTIVITY_EVENT';
