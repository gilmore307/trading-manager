-- Dedicated SQL contracts now own accepted model-input/business data shapes.
-- Retired preview CSV/JSON files under trading-data/storage/templates/data_kinds
-- are no longer evidence for active data_kind rows.

DELETE FROM trading_registry
WHERE kind = 'data_kind'
  AND path LIKE 'trading-data/storage/templates/data_kinds/%';

DELETE FROM trading_registry
WHERE kind = 'script'
  AND key = 'DATA_KIND_TEMPLATE_GENERATOR';
