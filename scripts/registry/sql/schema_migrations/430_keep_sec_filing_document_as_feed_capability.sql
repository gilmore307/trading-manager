-- Keep SEC filing document registered as a feed capability, not active final data_kind.

UPDATE trading_registry
SET kind = 'feed_capability',
    key = 'SEC_FILING_DOCUMENT',
    payload_format = 'text',
    payload = 'sec_filing_document',
    path = 'trading-data/src/data_feed/08_feed_sec_company_financials',
    applies_to = '08_feed_sec_company_financials;sec_company_financials;earnings_guidance_event_family;official_document_text',
    artifact_sync_policy = 'sync_artifact',
    note = 'Official SEC filing document metadata plus persisted text artifact, fetched by CIK, accession number, and document name for reviewed downstream result/guidance interpretation. Registered as feed capability rather than active final data_kind under the current registry boundary.',
    updated_at = NOW()
WHERE id = 'dki_OFH0JXSP';
