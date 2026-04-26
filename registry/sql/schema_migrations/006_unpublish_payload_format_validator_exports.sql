-- Payload-format validators are Python package utilities, not registry script surfaces.
-- Target engine: PostgreSQL.

DELETE FROM trading_registry
WHERE id IN (
  'scr_FMT2L9QA',
  'scr_FMV4K7RN',
  'scr_FMA8P3TZ'
);
