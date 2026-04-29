-- Remove bundle_05_option_expression component row timestamps from the active
-- registry after the contract switched to snapshot_time as the single
-- point-in-time clock.

DELETE FROM trading_registry
WHERE id IN ('fld_B05QTIM', 'fld_B05IVTM', 'fld_B05GRTM');
