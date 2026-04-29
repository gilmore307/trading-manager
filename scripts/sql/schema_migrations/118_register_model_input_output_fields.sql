-- Register current accepted model-input SQL output fields and attach shared
-- semantic fields to the new table contracts. Old manifest/config rows are gone;
-- these entries describe business output columns only.

UPDATE trading_registry SET applies_to = applies_to || ';market_regime_etf_bar;strategy_selection_symbol_bar_liquidity;position_execution_option_contract_timeseries', updated_at = CURRENT_TIMESTAMP
WHERE key = 'SYMBOL' AND applies_to NOT LIKE '%market_regime_etf_bar%';

UPDATE trading_registry SET applies_to = applies_to || ';market_regime_etf_bar;strategy_selection_symbol_bar_liquidity;position_execution_option_contract_timeseries', updated_at = CURRENT_TIMESTAMP
WHERE key = 'DATA_TIMEFRAME' AND applies_to NOT LIKE '%strategy_selection_symbol_bar_liquidity%';

UPDATE trading_registry SET applies_to = applies_to || ';market_regime_etf_bar;strategy_selection_symbol_bar_liquidity;position_execution_option_contract_timeseries', updated_at = CURRENT_TIMESTAMP
WHERE key = 'DATA_TIMESTAMP' AND applies_to NOT LIKE '%market_regime_etf_bar%';

UPDATE trading_registry SET applies_to = applies_to || ';market_regime_etf_bar;strategy_selection_symbol_bar_liquidity;position_execution_option_contract_timeseries', updated_at = CURRENT_TIMESTAMP
WHERE key IN ('OPEN_PRICE', 'HIGH_PRICE', 'LOW_PRICE', 'CLOSE_PRICE', 'VOLUME', 'TRADE_COUNT', 'VWAP')
  AND applies_to NOT LIKE '%market_regime_etf_bar%';

UPDATE trading_registry SET applies_to = applies_to || ';security_selection_us_equity_etf_holding', updated_at = CURRENT_TIMESTAMP
WHERE key IN ('ETF_SYMBOL', 'ISSUER_NAME', 'AS_OF_DATE', 'ETF_HOLDING_SYMBOL', 'ETF_HOLDING_NAME', 'ETF_HOLDING_WEIGHT', 'ETF_HOLDING_SHARES', 'ETF_HOLDING_MARKET_VALUE', 'SECTOR_TYPE')
  AND applies_to NOT LIKE '%security_selection_us_equity_etf_holding%';

UPDATE trading_registry SET applies_to = applies_to || ';security_selection_us_equity_etf_holding', updated_at = CURRENT_TIMESTAMP
WHERE key IN ('UNIVERSE_TYPE', 'EXPOSURE_TYPE')
  AND applies_to NOT LIKE '%security_selection_us_equity_etf_holding%';

UPDATE trading_registry SET applies_to = applies_to || ';strategy_selection_symbol_bar_liquidity', updated_at = CURRENT_TIMESTAMP
WHERE key IN ('QUOTE_COUNT', 'QUOTE_AVG_BID', 'QUOTE_AVG_ASK', 'QUOTE_AVG_SPREAD', 'QUOTE_LAST_BID', 'QUOTE_LAST_ASK')
  AND applies_to NOT LIKE '%strategy_selection_symbol_bar_liquidity%';

UPDATE trading_registry SET applies_to = applies_to || ';option_expression_contract_snapshot;position_execution_option_contract_timeseries', updated_at = CURRENT_TIMESTAMP
WHERE key IN ('OPTION_UNDERLYING', 'OPTION_EXPIRATION', 'OPTION_RIGHT_TYPE', 'OPTION_STRIKE')
  AND applies_to NOT LIKE '%option_expression_contract_snapshot%';

UPDATE trading_registry SET applies_to = applies_to || ';option_expression_contract_snapshot', updated_at = CURRENT_TIMESTAMP
WHERE key IN ('SNAPSHOT_TIME', 'OPTION_CONTRACT_COUNT', 'OPTION_CONTRACTS')
  AND applies_to NOT LIKE '%option_expression_contract_snapshot%';

UPDATE trading_registry SET applies_to = applies_to || ';event_overlay_event', updated_at = CURRENT_TIMESTAMP
WHERE key IN ('EVENT_ID', 'EVENT_TIME', 'SUMMARY', 'SOURCE_NAME', 'SYMBOL', 'SECTOR_TYPE')
  AND applies_to NOT LIKE '%event_overlay_event%';

UPDATE trading_registry SET applies_to = applies_to || ';event_overlay_event', updated_at = CURRENT_TIMESTAMP
WHERE key = 'TITLE' AND applies_to NOT LIKE '%event_overlay_event%';

UPDATE trading_registry SET applies_to = applies_to || ';event_overlay_event;security_selection_us_equity_etf_holding;stock_etf_exposure_template', updated_at = CURRENT_TIMESTAMP
WHERE key = 'STOCK_ETF_AVAILABLE_TIME' AND applies_to NOT LIKE '%event_overlay_event%';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('fld_MI6OPT01', 'identity_field', 'OPTION_SYMBOL', 'text', 'option_symbol', NULL, 'option_expression_contract_snapshot;position_execution_option_contract_timeseries', 'sync_artifact', 'Canonical normalized option contract symbol used after contract identity is known or reconstructable'),
  ('fld_MI3LIQ01', 'field', 'DOLLAR_VOLUME', 'text', 'dollar_volume', NULL, 'strategy_selection_symbol_bar_liquidity', 'sync_artifact', 'Bar-level notional traded value used as liquidity evidence'),
  ('fld_MI3LIQ02', 'field', 'QUOTE_AVG_BID_SIZE', 'text', 'avg_bid_size', NULL, 'strategy_selection_symbol_bar_liquidity', 'sync_artifact', 'Average bid size observed across quotes in the bar interval'),
  ('fld_MI3LIQ03', 'field', 'QUOTE_AVG_ASK_SIZE', 'text', 'avg_ask_size', NULL, 'strategy_selection_symbol_bar_liquidity', 'sync_artifact', 'Average ask size observed across quotes in the bar interval'),
  ('fld_MI3LIQ04', 'field', 'QUOTE_SPREAD_BPS', 'text', 'spread_bps', NULL, 'strategy_selection_symbol_bar_liquidity', 'sync_artifact', 'Average bid/ask spread expressed in basis points for a liquidity interval'),
  ('fld_MI5SNP01', 'classification_field', 'SNAPSHOT_ROLE', 'text', 'snapshot_role', NULL, 'option_expression_contract_snapshot', 'sync_artifact', 'Role of an option-chain snapshot in the strategy timeline, such as entry or exit'),
  ('fld_MI7EVT01', 'classification_field', 'INFORMATION_ROLE', 'text', 'information_role', NULL, 'event_overlay_event', 'sync_artifact', 'Event information role for model use, such as lagging_evidence or prior_signal'),
  ('fld_MI7EVT02', 'classification_field', 'EVENT_CATEGORY', 'text', 'event_category', NULL, 'event_overlay_event', 'sync_artifact', 'Event overview category such as macro_data, macro_news, sector_news, symbol_news, sec_filing, option_abnormal_activity, or equity_abnormal_activity'),
  ('fld_MI7EVT03', 'classification_field', 'SCOPE_TYPE', 'text', 'scope_type', NULL, 'event_overlay_event', 'sync_artifact', 'Event scope axis: macro, sector, or symbol'),
  ('fld_MI7EVT04', 'classification_field', 'REFERENCE_TYPE', 'text', 'reference_type', NULL, 'event_overlay_event', 'sync_artifact', 'Type of event detail locator, such as web_url, sec_file_path, internal_artifact_path, or source_reference'),
  ('fld_MI7EVT05', 'path_field', 'EVENT_REFERENCE', 'text', 'reference', NULL, 'event_overlay_event', 'sync_artifact', 'Primary locator for event details; may be a web URL, SEC file path, or internal artifact path')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = CURRENT_TIMESTAMP;
