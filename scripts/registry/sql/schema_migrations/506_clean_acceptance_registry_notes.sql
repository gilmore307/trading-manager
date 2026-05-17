-- Clean remaining current registry prose to use acceptance terminology.
-- Durable receipt identifiers embedded in payloads are historical evidence and are not rewritten.

UPDATE trading_registry
SET note = replace(
  replace(
    replace(note, 'production-promotion closeout', 'production-promotion acceptance'),
    'promotion closeout decision receipts', 'promotion acceptance decision receipts'
  ),
  'reviewer-agent closeout', 'reviewer-agent acceptance'
)
WHERE note ILIKE '%closeout%';

UPDATE trading_registry
SET note = replace(note, 'reviewed closeout', 'reviewed acceptance')
WHERE note ILIKE '%reviewed closeout%';
