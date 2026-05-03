-- Qualify the equity abnormal activity source_refs field key so the registry key is not an overly broad generic name.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET key = 'EQUITY_ABNORMAL_ACTIVITY_SOURCE_REFS',
    note = 'Compact source references for bars, liquidity windows, sector benchmark, and detection run used for the abnormal activity event'
WHERE id = 'fld_ABN008';
