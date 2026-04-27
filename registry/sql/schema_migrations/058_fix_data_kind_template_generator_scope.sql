-- Correct the data-kind template generator scope after moving templates under trading-data/storage/templates.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET applies_to = 'trading-data/storage/templates/data_kinds'
WHERE kind = 'script'
  AND key = 'DATA_KIND_TEMPLATE_GENERATOR';
