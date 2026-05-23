-- Register the accepted canonical model horizon grid.
--
-- Public model horizons are now 10min, 1h, 1D, and 1W. 1D is a rolling
-- 24-hour natural-time horizon and 1W is a rolling 7-calendar-day horizon.
-- Equity/ETF labels observe tradable path inside those natural-time windows;
-- crypto labels observe continuous path.

UPDATE trading_registry
SET payload = '10min;1h;1D;1W',
    note = 'Sparse TargetStateVector synchronized state-observation windows for market, sector, target, and cross-state blocks. Current windows are 10min, 1h, 1D, and 1W; these are state observation windows, not downstream action variants.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TARGET_STATE_VECTOR_SYNCHRONIZED_STATE_WINDOWS';

UPDATE trading_registry
SET payload = '10min;1h;1D;1W',
    note = 'Accepted EventFailureRiskModel horizons aligned with downstream alpha/position/action horizons. 1D is a rolling 24-hour natural-time horizon and 1W is a rolling 7-calendar-day horizon.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'EVENT_FAILURE_RISK_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = '10min;1h;1D;1W',
    note = 'Accepted AlphaConfidenceModel prediction horizons. 1D is a rolling 24-hour natural-time horizon and 1W is a rolling 7-calendar-day horizon; label builders must use point-in-time evidence and purge/embargo controls.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'ALPHA_CONFIDENCE_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = '10min;1h;1D;1W',
    note = 'Accepted PositionProjectionModel projection horizons. 1D is a rolling 24-hour natural-time horizon and 1W is a rolling 7-calendar-day horizon; projection labels must use purge/embargo controls.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'POSITION_PROJECTION_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = '10min;1h;1D;1W',
    note = 'Accepted UnderlyingActionModel horizons for Layer 8. 1D is a rolling 24-hour natural-time horizon and 1W is a rolling 7-calendar-day horizon.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'UNDERLYING_ACTION_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = '10min;1h;1D;1W',
    note = 'Accepted OptionExpressionModel horizons. 1D is a rolling 24-hour natural-time horizon and 1W is a rolling 7-calendar-day horizon; label builders must use purge/embargo controls.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'OPTION_EXPRESSION_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = '10min;1h;1D;1W',
    note = 'Accepted EventRiskGovernor event-context horizons. Horizons are context-observation horizons, not trade-action variants.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'EVENT_CONTEXT_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = '10min:3-7_no_0dte;1h:7-14;1D:7-21;1W:21-45',
    note = 'Accepted conservative Layer 9 DTE policy tied to Layer 8 holding-time assumptions. V1 avoids 0DTE and extreme short-DTE lottery contracts.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'OPTION_EXPRESSION_DTE_POLICY';

UPDATE trading_registry
SET note = 'Layer 1/2 market-context ETF bar source. Downloads only canonical 1Min raw Alpaca bars into trading_data.source_01_market_regime; downstream feature_generation derives 1min, 10min, 1h, and 1d evidence locally. Provider-native multi-frame rows must not be mixed into this source table.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SOURCE_01_MARKET_REGIME';

UPDATE trading_registry
SET note = 'Layer 1 row identity field for the point-in-time input frame used to build market-state evidence, such as 1min, 10min, 1h, or 1d.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'INPUT_FRAME';

UPDATE trading_registry
SET note = 'Layer 1 row identity field for the forecast horizon evaluated from the current input frame, such as 10min, 1h, 1D, or 1W.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'PREDICTION_HORIZON';
