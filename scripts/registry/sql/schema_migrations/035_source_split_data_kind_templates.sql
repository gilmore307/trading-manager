-- Split data-kind templates by source folder and update registry locators.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  path = 'trading-data/templates/data_kinds/alpaca/README.md',
  note = CASE key
    WHEN 'DATA_KIND_TEMPLATE_DATA_KIND' THEN 'canonical registered data_kind payload/key documented by a source-specific final saved data-kind template entry'
    WHEN 'DATA_KIND_TEMPLATE_SOURCE' THEN 'provider or official source for a source-specific final saved data-kind template entry'
    WHEN 'DATA_KIND_TEMPLATE_BUNDLE' THEN 'execution data_bundle that fetches or produces the final saved data kind in a source-specific template README'
    WHEN 'DATA_KIND_TEMPLATE_STATUS' THEN 'implementation/availability status for a source-specific final saved data-kind template entry'
    WHEN 'DATA_KIND_TEMPLATE_PERSISTENCE_POLICY' THEN 'persistence rule for final saved data and any raw/transient inputs in a source-specific template README'
    WHEN 'DATA_KIND_TEMPLATE_EARLIEST_AVAILABLE_RANGE' THEN 'earliest confirmed provider range or smoke-confirmed sample range in a source-specific template README'
    WHEN 'DATA_KIND_TEMPLATE_DEFAULT_TIMESTAMP_SEMANTICS' THEN 'timezone and timestamp field semantics for normalized final saved rows in a source-specific template README'
    WHEN 'DATA_KIND_TEMPLATE_NATURAL_GRAIN' THEN 'natural row grain such as one bar, article, contract/day, or interval aggregate in a source-specific template README'
    WHEN 'DATA_KIND_TEMPLATE_REQUEST_PARAMETERS' THEN 'required and important optional request parameters for the final saved data kind in a source-specific template README'
    WHEN 'DATA_KIND_TEMPLATE_PAGINATION_RANGE_BEHAVIOR' THEN 'pagination, segmentation, and range behavior for fetching or producing the data kind in a source-specific template README'
    WHEN 'DATA_KIND_TEMPLATE_PREVIEW_FILE' THEN 'small CSV preview/template file in the source-specific folder for the final saved data-kind schema'
    WHEN 'DATA_KIND_TEMPLATE_KNOWN_CAVEATS' THEN 'entitlements, quirks, high-volume risks, or hardening notes for a data kind in a source-specific template README'
    ELSE note
  END
WHERE kind = 'field'
  AND applies_to = 'data_kind_template'
  AND key LIKE 'DATA_KIND_TEMPLATE_%';

UPDATE trading_registry
SET path = 'trading-data/templates/data_kinds/alpaca/equity_bar.preview.csv'
WHERE kind = 'data_kind'
  AND key = 'EQUITY_BAR';

UPDATE trading_registry
SET path = 'trading-data/templates/data_kinds/alpaca/equity_liquidity_bar.preview.csv'
WHERE kind = 'data_kind'
  AND key = 'EQUITY_LIQUIDITY_BAR';

UPDATE trading_registry
SET path = 'trading-data/templates/data_kinds/alpaca/equity_news.preview.csv'
WHERE kind = 'data_kind'
  AND key = 'EQUITY_NEWS';
