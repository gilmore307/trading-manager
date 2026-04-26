-- Register data-kind template README fields and align bundle/data-kind paths.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_EKIND001', 'field', 'DATA_KIND_TEMPLATE_DATA_KIND', 'field_name', 'data_kind', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'canonical registered data_kind payload/key documented by a final saved data-kind template entry'),
  ('fld_EKIND002', 'field', 'DATA_KIND_TEMPLATE_SOURCE', 'field_name', 'source', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'provider or official source for a final saved data-kind template entry'),
  ('fld_EKIND003', 'field', 'DATA_KIND_TEMPLATE_BUNDLE', 'field_name', 'bundle', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'execution data_bundle that fetches or produces the final saved data kind'),
  ('fld_EKIND004', 'field', 'DATA_KIND_TEMPLATE_STATUS', 'field_name', 'status', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'implementation/availability status for a final saved data-kind template entry'),
  ('fld_EKIND005', 'field', 'DATA_KIND_TEMPLATE_PERSISTENCE_POLICY', 'field_name', 'persistence_policy', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'persistence rule for final saved data and any raw/transient inputs'),
  ('fld_EKIND006', 'field', 'DATA_KIND_TEMPLATE_EARLIEST_AVAILABLE_RANGE', 'field_name', 'earliest_available_range', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'earliest confirmed provider range or smoke-confirmed sample range'),
  ('fld_EKIND007', 'field', 'DATA_KIND_TEMPLATE_DEFAULT_TIMESTAMP_SEMANTICS', 'field_name', 'default_timestamp_semantics', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'timezone and timestamp field semantics for normalized final saved rows'),
  ('fld_EKIND008', 'field', 'DATA_KIND_TEMPLATE_NATURAL_GRAIN', 'field_name', 'natural_grain', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'natural row grain such as one bar, article, contract/day, or interval aggregate'),
  ('fld_EKIND009', 'field', 'DATA_KIND_TEMPLATE_REQUEST_PARAMETERS', 'field_name', 'request_parameters', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'required and important optional request parameters for the final saved data kind'),
  ('fld_EKIND010', 'field', 'DATA_KIND_TEMPLATE_PAGINATION_RANGE_BEHAVIOR', 'field_name', 'pagination_range_behavior', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'pagination, segmentation, and range behavior for fetching or producing the data kind'),
  ('fld_EKIND011', 'field', 'DATA_KIND_TEMPLATE_PREVIEW_FILE', 'field_name', 'preview_file', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'small CSV preview/template file for the final saved data-kind schema'),
  ('fld_EKIND012', 'field', 'DATA_KIND_TEMPLATE_KNOWN_CAVEATS', 'field_name', 'known_caveats', 'trading-data/templates/data_kinds/README.md', 'data_kind_template', 'entitlements, quirks, high-volume risks, or hardening notes for a data kind')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

UPDATE trading_registry
SET
  key = 'ALPACA_LIQUIDITY',
  payload = 'alpaca_liquidity',
  path = 'trading-data/src/trading_data/data_sources/alpaca_liquidity',
  applies_to = 'trading-data',
  note = 'historical Alpaca liquidity bundle that uses transient trades/quotes to produce equity_liquidity_bar; task/run IDs should use alpaca_liquidity-specific prefixes'
WHERE id = 'dbu_BR96XL13'
  AND kind = 'data_bundle';

UPDATE trading_registry
SET
  path = 'trading-data/src/trading_data/data_sources/alpaca_bars',
  note = 'historical stock/ETF bars bundle; task/run IDs should use alpaca_bars-specific prefixes'
WHERE id = 'dbu_MMC41ETB'
  AND kind = 'data_bundle';

UPDATE trading_registry
SET
  path = 'trading-data/src/trading_data/data_sources/alpaca_news',
  note = 'historical Alpaca stock/ETF news bundle; task/run IDs should use alpaca_news-specific prefixes'
WHERE id = 'dbu_UF1ZH2YB'
  AND kind = 'data_bundle';

UPDATE trading_registry
SET
  path = 'trading-data/src/trading_data/data_sources/macro_data'
WHERE kind = 'data_bundle'
  AND key = 'MACRO_DATA';

UPDATE trading_registry
SET
  path = 'trading-data/templates/data_kinds/equity_bar.preview.csv',
  applies_to = 'alpaca_bars',
  note = 'Final persisted stock/ETF OHLCV bar; template path points to the accepted final CSV shape'
WHERE kind = 'data_kind'
  AND key = 'EQUITY_BAR';

UPDATE trading_registry
SET
  path = 'trading-data/templates/data_kinds/equity_liquidity_bar.preview.csv',
  applies_to = 'alpaca_liquidity',
  note = 'Final persisted stock/ETF liquidity bar aggregated from transient raw trades and quotes; template path points to the accepted final CSV shape'
WHERE kind = 'data_kind'
  AND key = 'EQUITY_LIQUIDITY_BAR';

UPDATE trading_registry
SET
  path = 'trading-data/templates/data_kinds/equity_news.preview.csv',
  applies_to = 'alpaca_news',
  note = 'Final persisted Alpaca stock/ETF news row; template path points to the accepted final CSV shape'
WHERE kind = 'data_kind'
  AND key = 'EQUITY_NEWS';

UPDATE trading_registry
SET
  path = NULL,
  applies_to = 'alpaca_liquidity',
  note = CASE key
    WHEN 'EQUITY_TRADE' THEN 'Alpaca trade prints are live-confirmed transient inputs for alpaca_liquidity, not default persisted final outputs; no data-kind template until explicitly accepted as saved data'
    WHEN 'EQUITY_QUOTE' THEN 'Alpaca quote records are live-confirmed transient inputs for alpaca_liquidity, not default persisted final outputs; no data-kind template until explicitly accepted as saved data'
    WHEN 'EQUITY_SNAPSHOT' THEN 'Alpaca snapshots are live-confirmed but not currently accepted as final saved outputs; no data-kind template until explicitly accepted as saved data'
    ELSE note
  END
WHERE kind = 'data_kind'
  AND key IN ('EQUITY_TRADE', 'EQUITY_QUOTE', 'EQUITY_SNAPSHOT');
