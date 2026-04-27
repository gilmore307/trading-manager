-- Register implemented SEC company financials bundle path.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_sources/sec_company_financials',
    artifact_sync_policy = 'sync_artifact',
    note = 'Implemented historical SEC EDGAR company financials bundle for submissions, companyfacts, companyconcept, and XBRL frames; persists compact normalized CSV outputs and request manifests while avoiding bulky raw SEC response persistence by default'
WHERE kind = 'data_bundle'
  AND key = 'SEC_COMPANY_FINANCIALS';
