-- Register SEC EDGAR as the official provider/source for company financial reporting data.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_OIF1JM3D', 'term', 'SEC_EDGAR', 'text', 'U.S. Securities and Exchange Commission EDGAR APIs and filings source for public company submissions, XBRL facts, and financial reporting data', 'https://www.sec.gov/search-filings/edgar-application-programming-interfaces', 'trading-data', 'official SEC source; no credential or secret alias is registered, but automated access must follow SEC fair-access requirements including an identifying User-Agent'),
  ('trm_20PZRDY8', 'term', 'SEC_COMPANY_FINANCIALS', 'text', 'Historical trading-data bundle for company financial report data from SEC EDGAR company facts, submissions, and related filing metadata', 'https://www.sec.gov/search-filings/edgar-application-programming-interfaces', 'trading-data', 'bundle planning term; preferred bundle key is sec_company_financials and task/run IDs should use sec_company_financials-specific prefixes')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
